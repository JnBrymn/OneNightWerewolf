These are small bugs that we will eventually want to tackle, but they aren't immediately urgent:
1. ~~(somewhat urgent) If someone takes the insomniac role... only let players act based upon their original role.~~ FIXED: night actions keyed by initial_role; Troublemaker no longer swaps night_action_completed.
2. Wehn the Seer looks at a player's role, the player's name changes to the uuid
3. The insomniac can not click OK to let the night phase be over
4. Lone Werewolf gets stuck after making card choice - after ok'in the card viewed, a box pops up that says "Loading your werewolf information..."
5. ~~Robber's role should change after it's role, but it shouldn't take the behavior of the other role later (similar to 1)~~ FIXED: same as 1.
6. ~~Why does the troublemaker say "you are the insomniac and your role is ..."?~~ FIXED: RoleActionHandler uses currentRoleStep only when it's this player's turn (role === currentRoleStep), so Insomniac UI no longer shown to Troublemaker when step is Insomniac.
7. ~~The werewolf's information says "You viewed Player2's card. It is: Werewolf"~~ FIXED: action_service now emits "There are 2 werewolves, the other is Steve" (or "Your fellow werewolves are: A, B" for 3+) for fellow-werewolf VIEW_CARDs.
8. For the scripts/dev_seed_game.py script Make it update the database so that we're already past the acknowledgement of roles step and we can immediately start the game. 
9. For the minion, after you see the werewolves, the information says "You are a Werewolf." But the truth is the minion is not a werewolf. It just needs to know what the other werewolves are because it's on the werewolf team. It's a minion. 
10. Any sort of a tie between two people or more does not result in killing anybody, and thus the werewolf wins if there is one OR the villiagers win if there is no werewolves 
11. For voting, I would like the vote to be an overlay and not use the "alert" box.