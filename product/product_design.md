# One Night Werewolf - Product Design Document

## Overview
A digital implementation of the One Night Ultimate Werewolf card game, built as a Next.js React app with a FastAPI backend.

---

## Game Flow

1. **Lobby Phase**: Players join/create a game (outside game state)
2. **Game States** (within game):
   - **NIGHT**: Roles wake up in sequence and perform actions
   - **DAY_DISCUSSION**: Discussion phase with timer
   - **DAY_VOTING**: Simultaneous voting (no discussion)
   - **RESULTS**: Winners determined, scores updated, round ends
3. **Next Game**: Option to play another game in the same Game Set (creates new game, shuffles cards, assigns new roles, goes to NIGHT) or end game set

**Multi-Game Sessions**: Groups can play multiple games together in a Game Set, with cumulative score tracking across all games. Each game cycles through: NIGHT → DAY_DISCUSSION → DAY_VOTING → RESULTS. After RESULTS, players can start a new game in the same Game Set (cards shuffled, roles randomly reassigned).

---

## Frontend Components (React/Next.js)

### 1. **Lobby System**
- **Create Game Page**: Any player creates a new game room
  - Specify number of players
  - Select role collection (choose from available roles: Villager, Robber, Troublemaker, Seer, Werewolf, Minion, Mason, Drunk, Insomniac, Tanner, Hunter)
  - System automatically ensures: number of cards = number of players + 3
  - Chat available for communication
- **Join Game Page**: Players enter game code/ID to join
  - Chat available for communication
- **Game Lobby**: Waiting room showing connected players
  - Player list showing all joined players
  - Start game button (enabled when specified number of players have joined)
  - Leave game option
  - Shows selected role collection (but not which specific cards)
  - Discussion timer setting (time limit for Day Phase discussion)
  - Chat available for communication

### 2. **Game Room**
- **Main Game Container**: Orchestrates all game phases
- **Visual Game Board**: 
  - Player avatars (user images/logos/photos) arranged around board
  - Player cards visible next to each avatar (for swapping actions during night phase)
  - Center cards area (3 cards exist but are hidden/secret - shown as face-down placeholders)
  - Cards show role names when revealed (face-up for actions, hidden during discussion)
- **Host** (Automated): 
  - Automated host persona with recorded audio instructions
  - Host calls each role in sequence following rigid script (like traditional game announcer)
  - Role action completion indicator (e.g., "Seer action complete" - does not reveal which players)
  - Host automatically advances to next role when current role's action(s) complete
  - Optional timer controls for phases
- **Game & Score Display**:
  - Current game number indicator (Game 1, Game 2, etc. within Game Set)
  - Cumulative score board (wins/losses per player across all games in Game Set) - visible during all phases
- **Phase Indicator**: Shows current game state (Night, Day Discussion, Day Voting, Results)
- **Action Status**: Shows role-based completion (e.g., "Seer action complete") without revealing which players have which roles

### 3. **Role Assignment UI**
- **Initial Role Reveal**: At start of game (before NIGHT phase), each player sees their own assigned role
  - Role card displayed with role name and instructions
  - Brief explanation of role abilities
  - Player acknowledges they've seen their role
- **Role Hidden After Reveal**: Once player acknowledges, their role card becomes hidden/face-down
  - Role may change during night phase (via swaps), so it stays hidden
  - Player can only see their role again if their role allows viewing (e.g., Insomniac)
- **Center Cards**: Never revealed - remain secret throughout game (shown as face-down placeholders)

### 4. **Night Phase UI**
- **General State** (when not your turn):
  - Players see that night phase is happening
  - Host audio plays for current role being called
  - No specific information revealed until it's their turn
  - Chat available for communication (though typically quiet during night phase)
  - Chat available for communication (though typically quiet during night phase)
- **Role-Specific Turn Display** (when it's your role's turn):
  - **Automatic Information Roles** (no action required):
    - **Werewolves** (multiple): Automatically shown who all other werewolves are
    - **Werewolf** (lone wolf - only one werewolf): Must choose which center card to view (action required)
    - **Minion**: Automatically shown who all the werewolves are
    - **Masons**: Automatically shown who the other mason is (or that other mason is in center)
  - **Action Required Roles**:
    - **Seer**: Role-specific instructions displayed - choose to view one player card OR two center cards
    - **Robber**: Role-specific instructions displayed - select player card to exchange with (swap cards, then view new card)
    - **Troublemaker**: Role-specific instructions displayed - select two other player cards to swap (no viewing)
    - **Drunk**: Role-specific instructions displayed - select center card to exchange with (no viewing of new card)
    - **Werewolf (Lone Wolf)**: Role-specific instructions displayed - select one center card to view (their choice)
    - **Insomniac**: Role-specific instructions displayed - view own current card
- **Action Feedback**: Visual confirmation when action completes
- **Center Cards**: Shown as face-down placeholders - only revealed when a role action allows viewing

### 5. **Day Phase UI**
- **Day Phase Sub-Phases**:
  - A. **Discussion Phase**:
    - Game board visible (cards face-down during discussion)
    - Chat actively used for discussion and strategy
    - Timer countdown showing remaining discussion time (set during game creation)
    - Host automatically transitions to Voting when timer expires
  - B. **Voting Phase**:
    - Discussion ends - chat disabled or restricted during voting
    - Voting Interface:
      - Click player avatar/card to vote
      - Vote confirmation dialog
      - Vote status display (who voted for whom, updated in real-time)
      - All players vote simultaneously (no discussion allowed)
    - Host automatically advances to Results when all votes cast
- **Vote Results Display**: Shows final vote counts when voting completes

### 6. **Results Phase UI**
- **Results Screen**: 
  - Current game results:
    - Who died (if anyone)
    - Final role assignments (after all night actions)
    - Team assignments (Village team, Werewolf team, or Other/Tanner)
    - Winners announcement (based on team and win conditions)
  - **Cumulative Score Board**: 
    - Player list with win/loss count across all games in Game Set
    - Current game number
    - Win/loss indicators for each player (whether they were on winning team)
  - Chat available for post-game discussion
- **Game Summary**: Breakdown of what happened in current game
- **Action Options** (after reviewing results):
  - **Play Another Game Button**: Start another game in the same Game Set (creates new game, shuffles cards, assigns new roles, goes to NIGHT state)
  - **End Game Set Button**: End game set and return to lobby

### 7. **Shared Components**
- **Player Avatar**: Visual representation of player (image/logo/photo)
- **Card Component**: Reusable card UI for roles (face-up/face-down states)
- **Game Board Layout**: Arranges players and center cards visually
- **Drag and Drop**: For card swapping actions (optional, can use click/select)
- **Modal/Dialog**: For actions and confirmations
- **Chat Component**: 
  - **Always Available**: Persistent chat interface visible on all screens and phases
  - Text chat (MVP) - available in all game states (Night, Day Discussion, Day Voting, Results)
  - Chat history persists throughout game session
  - Future: Audio/RTC support for voice communication
  - Far Future: built-in video of players
- **Toast Notifications**: For game events and errors
- **Loading States**: For async operations

---

## Backend API (FastAPI)

### 1. **Game Management Endpoints**
- `POST /api/games` - Create new game
- `GET /api/games/{game_id}` - Get game state
- `POST /api/games/{game_id}/join` - Join game
- `POST /api/games/{game_id}/leave` - Leave game
- `POST /api/games/{game_id}/start` - Start game (when minimum number of players have joined)
- `POST /api/game-sets/{game_set_id}/games` - Create new game in game set (from Results state of previous game, creates new game in NIGHT state)
- `POST /api/game-sets/{game_set_id}/end` - End game set (from Results state, ends game set)
- `GET /api/games/{game_id}/players` - List players
- `GET /api/games/{game_id}/scores` - Get cumulative scores for all players

### 2. **Game State Management**
- **Game State Machine**: 
  - States: `NIGHT` → `DAY_DISCUSSION` → `DAY_VOTING` → `RESULTS`
  - Each game is independent and cycles through these states once
  - After `RESULTS`, players can choose to start a new game in the same Game Set or end the Game Set
  - If continuing: creates a new game (new game_id) with shuffled cards and new role assignments, starts in `NIGHT` state
  - If ending: Game Set ends (returns to lobby outside of game state)
- **Game Set Tracking**: Track which games belong to which Game Set
- **State Transitions**: Handle phase changes within a game
- **Player State**: Track player actions, votes within each game
- **Score Tracking**: Update cumulative scores after each game completes

### 3. **Role Assignment Service**
- **Role Selection**: Game creator selects which roles are in the collection (from available roles)
- **Card Count Logic**: 
  - Number of cards = number of players + 3
  - Cards are randomly drawn from selected role collection
  - Random assignment of cards to players
  - Remaining 3 cards go to center (kept secret)
- **Role Assignment Endpoints**:
  - `POST /api/games/{game_id}/assign-roles` - Randomly assign roles from collection
  - `GET /api/games/{game_id}/my-role` - Get player's own role (only visible to that player)
  - Center cards never exposed via API (only used internally for night actions)

### 4. **Gameplay Phase Orchestration**
- **Host (Automated)**: Host persona automatically advances phases following rigid script
- **Action Status Tracking**:
  - `GET /api/games/{game_id}/action-status` - Get role-based completion status (e.g., "Seer: complete", "Werewolves: complete") without revealing player identities
  - Host monitors completion and automatically advances when all required actions complete
- **Night Phase Manager**:
  - **Wake Order Manager**: Host automatically calls roles in correct sequence following rigid script
    1. Werewolves
    2. Minion
    3. Masons
    4. Seer
    5. Robber
    6. Troublemaker
    7. Drunk
    8. Insomniac
  - Host calls each role in sequence (via text on screen originally and eventually by recorded audio)
  - **Information Display Roles** (automatic, no action required):
    - **Werewolves** (multiple - 2+): System automatically displays to all werewolves who the other werewolves are
    - **Minion**: System automatically displays to minion who all the werewolves are
    - **Masons**: System automatically displays to masons who the other mason is (or that other mason is in center)
    - These roles complete immediately (no waiting for player action - the indicators remain on their screen throughout the game)
  - **Action Required Roles**:
    - **Werewolf (Lone Wolf - only 1 werewolf)**: Must choose which center card to view (player's choice, action required)
    - **Seer**: View one player card OR 2 center cards (no moving)
    - **Robber**: Exchange card with player (swap) AND view new card
    - **Troublemaker**: Exchange two other players' cards (no viewing)
    - **Drunk**: Exchange with center card (no viewing)
    - **Insomniac**: View own current card
  - **Action Validation**: Ensure actions are valid (correct targets, no duplicates)
  - **Action Completion Tracking**: Track which players have completed required actions (backend only - never exposed to frontend)
  - **Role Completion Status**: Aggregate player completions into role-based status (e.g., "Seer has acted") for host progression
  - **Host Progression**: Host automatically advances to next role when current role completes (immediate for info roles, after action for action roles)
  - **State Updates**: Apply actions to game state (card swaps, views)
- **Day Phase Manager**:
  - **Discussion Phase**:
    - Timer countdown (time limit set during game creation)
    - Chat enabled for discussion
    - Host automatically transitions to Voting when timer expires
  - **Voting Phase**:
    - **Voting System**:
      - `POST /api/games/{game_id}/vote` - Submit vote
      - `GET /api/games/{game_id}/votes` - Get current votes
    - Chat disabled/restricted during voting (no discussion)
    - All players vote simultaneously
    - **Vote Counting**: Determine who dies (tie resolution)
    - **Host Progression**: Host automatically advances to Results when all votes cast

### 6. **Win Condition Logic**
- **Team Assignment**: Determine final team for each player
- **Death Resolution**: Apply deaths (including Hunter effect)
- **Win Check**:
  - Village wins: At least one Werewolf dies
  - Werewolves win: No Werewolves die
  - Tanner wins: Tanner dies
  - Minion special cases
    - If Minion dies and no Werewolves die → Werewolves win
    - If no players are Werewolves and Minion dies → Minion wins if at least one other player dies
- **Score Recording**: After win determination, record game results for all players
  - `POST /api/games/{game_id}/scores` - Record game scores
  - `GET /api/game-sets/{game_set_id}/scores` - Get cumulative scores for all players across all games in set

### 7. **Real-time Communication**
- **WebSocket Support**: For live updates and chat
- **Event Broadcasting**: Notify all players of state changes
- **Action Synchronization**: Ensure all players see same state
- **Chat System**: 
  - `POST /api/games/{game_id}/chat` - Send chat message
  - `GET /api/games/{game_id}/chat` - Get chat history
  - Real-time chat via WebSocket
- **Future: Audio/RTC**: Voice communication support (WebRTC or similar)

---

## Data Persistence

### 1. **Game Set Storage** (Groups multiple games together)
- **Game Set Table**:
  - `game_set_id` (UUID, primary key)
  - `created_by` (user/session ID of game set creator)
  - `num_players` (integer: number of players in this set)
  - `selected_roles` (JSON: array of role names selected for games in this set)
  - `discussion_timer_seconds` (integer: discussion time limit)
  - `created_at`, `updated_at`
  - `ended_at` (timestamp: when game set ended, null if active)

### 2. **Game State Storage** (Each game is a single round)
- **Game Table**:
  - `game_id` (UUID, primary key)
  - `game_set_id` (foreign key: which game set this game belongs to)
  - `game_number` (integer: sequence number within game set, 1, 2, 3, etc.)
  - `state` (enum: NIGHT, DAY_DISCUSSION, DAY_VOTING, RESULTS)
  - `current_role_step` (which role in the night sequence is currently active - only set when state is NIGHT)
  - `created_at`, `updated_at`
  - `ended_at` (timestamp: when game ended)

### 3. **Player Identity** (Persistent across game sets)
- **Player Table**:
  - `player_id` (UUID, primary key)
  - `user_id` / `session_id` (who is playing)
  - `player_name`
  - `avatar_url` (optional: user image/logo/photo)
  - `created_at` (when player first joined)

### 4. **Player Role** (Game-specific state, one row per player per game)
- **Player Role Table**:
  - `player_role_id` (UUID, primary key)
  - `game_id` (foreign key: which game this role is for)
  - `player_id` (foreign key: which player)
  - `initial_role` (initial role assignment - only visible to that player)
  - `final_role` (after all night actions - revealed at Results phase)
  - `role_revealed` (boolean: whether player has seen their initial role)
  - `team` (village/werewolf/tanner)
  - `was_killed` (boolean: whether player was killed at end of game)

### 5. **Card Swaps** (Night Phase Mutations)
- **Card Swap Table**:
  - `swap_id` (UUID, primary key)
  - `game_id` (foreign key: which game this swap occurred in)
  - `swapper_player_role_id` (player_role_id: who performed the swap - Robber, Troublemaker, or Drunk)
  - `swap_type` (enum: PLAYER_TO_PLAYER, PLAYER_TO_CENTER, CENTER_TO_PLAYER)
  - `source_type` (enum: PLAYER, CENTER)
  - `source_player_role_id` (player_role_id if source is player, null if center)
  - `source_center_index` (0, 1, or 2 if source is center, null if player)
  - `target_type` (enum: PLAYER, CENTER)
  - `target_player_role_id` (player_role_id if target is player, null if center)
  - `target_center_index` (0, 1, or 2 if target is center, null if player)
  - `timestamp`
- **Note**: Card views (Seer, Werewolves, Minion, Masons, Insomniac) are not tracked - they are ephemeral information display only and don't mutate game state

### 6. **Votes**
- **Vote Table**:
  - `vote_id` (UUID, primary key)
  - `game_id` (foreign key: which game this vote occurred in)
  - `voter_player_role_id` (player_role_id: who voted)
  - `target_player_role_id` (player_role_id: who was voted for)
  - `timestamp`

### 7. **Center Cards** (Current state of the 3 center positions)
- **Center Card Table**:
  - `center_card_id` (UUID, primary key)
  - `game_id` (foreign key: which game these cards belong to)
  - `card_index` (0, 1, or 2)
  - `role` (role name - kept secret, never exposed to players, updated when swaps occur)
- **Note**: When a swap occurs (e.g., Drunk swaps with center card), update the center card's `role` to reflect the card that ends up in that center position. This table always represents the current state of the 3 center positions.
- **Privacy**: Center card roles are never revealed to players (only used internally for night actions like Seer viewing or Drunk swapping)

### 8. **Chat Messages** (Optional - can be ephemeral)
- **Chat Message Table**:
  - `message_id` (UUID, primary key)
  - `game_set_id` (foreign key: chat persists across games in a set)
  - `player_id` (who sent message)
  - `message` (text content)
  - `timestamp`

### 9. **Score Calculation** (Computed on-demand, no separate table)
- **Cumulative scores computed from existing tables**:
  - Query Player Role table for all games in a Game Set
  - Join with Votes table to determine who died in each game
  - Apply win condition logic to determine winners for each game
  - Check if each player's team won (based on final_role, team, was_killed, and deaths)
  - Aggregate wins/losses per player across all games in the game set
- **No separate Game Score table needed** - all data exists in Player Role, Votes, and Game tables

---

## Technical Considerations

### Frontend
- **State Management**: Zustand for game state (preferred over Context API for better performance with frequent updates, minimal boilerplate, 4KB bundle size)
- **Real-time Updates**: WebSocket client for live game state and chat updates
- **Routing**: Next.js App Router for game pages (game page route: `/game/[game_set_id]`, player_id stored in session/cookies)
- **UI Framework**: Tailwind CSS
- **Animations**: For role reveals and phase transitions
- **Host Audio**: 
  - **MVP**: Text-based instructions with optional ping/notification sound to indicate player's turn
  - **Future**: Recorded audio files for host persona instructions (one recording per role call/instruction)

### Backend
- **API Framework**: FastAPI with async support
- **WebSockets**: FastAPI WebSocket support for real-time updates
- **Database**: SQLite (with SQLAlchemy ORM)
- **ORM**: SQLAlchemy
- **Validation**: Pydantic models for request/response

### Data Flow
1. Client sends action → API validates → Updates DB → Broadcast to all clients
2. WebSocket maintains connection for real-time updates (game state, chat)
3. Game state fetched on page load (game_set_id from URL `/game/[game_set_id]`, player_id from session/cookies), then updated via WebSocket
4. Host (automated) automatically advances phases when actions complete or timer expires (follows rigid script)
5. All players see synchronized game board state

---

## Key Game Logic Challenges

1. **Night Action Sequencing**: Ensuring actions happen in correct order during gameplay night phase
3. **State Consistency**: All players see same state
4. **Role Swapping**: Tracking role changes through gameplay night phase
5. **Team Assignment**: Determining final teams after all actions
6. **Win Conditions**: Handling edge cases (no werewolves, minion scenarios)
7. **Gameplay Phase Transitions**: Smoothly transitioning from night to day sub-phases

---

## MVP Scope

### Phase 1: Core Game Loop
- Basic roles: Werewolf, Villager, Seer, Robber, Troublemaker
- Gameplay phase with night sub-phase (basic actions)
- Gameplay phase with day sub-phase (voting)
- Simple win conditions

### Phase 2: Additional Roles
- Add remaining roles (Minion, Mason, Drunk, Insomniac, Tanner, Hunter)
- Handle complex interactions

### Phase 3: Polish
- Animations and transitions
- Game history and replays
- Custom role selection
- Timer options
