"""Service for computing game results and win conditions."""
from collections import Counter
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.player_role import PlayerRole
from models.vote import Vote
from models.player import Player


def get_results(db: Session, game_id: str) -> dict:
    """Compute deaths, winning team, and per-player results. Sets was_killed on player_roles."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")
    if game.state != GameState.RESULTS:
        raise ValueError(f"Game is not in results phase (state={game.state})")

    player_roles = db.query(PlayerRole).filter(PlayerRole.game_id == game_id).all()
    votes = db.query(Vote).filter(Vote.game_id == game_id).all()
    player_id_to_role = {pr.player_id: pr for pr in player_roles}

    # Vote counts per target
    vote_counts = Counter(v.target_player_id for v in votes)
    if not vote_counts:
        deaths = []
        vote_summary = {}
    else:
        max_votes = max(vote_counts.values())
        # Official rule: "If no player receives more than one vote, no one dies."
        # (e.g. everyone points right → each gets 1 vote → no one dies)
        if max_votes <= 1:
            deaths = []
        else:
            deaths = [pid for pid, count in vote_counts.items() if count == max_votes]
        vote_summary = {pid: count for pid, count in vote_counts.items()}

    # Hunter: if Hunter died, their vote target also dies
    hunter_votes = {v.voter_player_id: v.target_player_id for v in votes}
    for pr in player_roles:
        if pr.current_role == "Hunter" and pr.player_id in deaths:
            target_id = hunter_votes.get(pr.player_id)
            if target_id and target_id not in deaths:
                deaths.append(target_id)

    # Persist was_killed
    for pr in player_roles:
        pr.was_killed = pr.player_id in deaths
    db.commit()

    # Winning team
    werewolf_player_ids = {pr.player_id for pr in player_roles if pr.current_role == "Werewolf"}
    tanner_died = any(pr.player_id in deaths and pr.current_role == "Tanner" for pr in player_roles)
    any_werewolf_died = bool(werewolf_player_ids & set(deaths))
    minion_players = [pr for pr in player_roles if pr.current_role == "Minion"]
    no_werewolves_in_game = len(werewolf_player_ids) == 0

    if tanner_died:
        winning_team = "tanner"
    elif any_werewolf_died:
        winning_team = "village"
    elif no_werewolves_in_game and minion_players:
        # Instructions: "If no players are Werewolves, the Minion wins if one other player dies."
        # So: at least one non-Minion player must have died (Minion may or may not die, e.g. tie).
        other_player_died = any(
            pr.player_id in deaths and pr.current_role != "Minion" for pr in player_roles
        )
        if other_player_died:
            winning_team = "minion"
        else:
            # Only Minion died or no deaths: werewolf team wins (no werewolves died)
            winning_team = "werewolf"
    else:
        winning_team = "werewolf"

    # Per-player results: who won
    def player_won(pr: PlayerRole) -> bool:
        if winning_team == "tanner":
            return pr.current_role == "Tanner"
        if winning_team == "village":
            return pr.team == "village"
        if winning_team == "werewolf":
            return pr.team == "werewolf" or pr.current_role == "Minion"
        if winning_team == "minion":
            return pr.current_role == "Minion"
        return False

    players_out = []
    for pr in player_roles:
        player = db.query(Player).filter(Player.player_id == pr.player_id).first()
        players_out.append({
            "player_id": pr.player_id,
            "player_name": player.player_name if player else "Unknown",
            "initial_role": pr.initial_role,
            "current_role": pr.current_role,
            "team": pr.team or "village",
            "died": pr.player_id in deaths,
            "won": player_won(pr),
        })

    return {
        "deaths": deaths,
        "winning_team": winning_team,
        "players": players_out,
        "vote_summary": vote_summary,
    }
