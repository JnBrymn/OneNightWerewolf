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

### 2. **Unified Game Screen** (Single Screen for All Game Phases)
- **Single Adaptive Screen**: One game screen that works through all game states (NIGHT, DAY_DISCUSSION, DAY_VOTING) using the game's `state` and `current_role_step` fields to determine what's visible and active
- **Always Visible Elements**:
  - **All Players**: All players in the game are displayed as clickable buttons/avatars arranged around the board
    - Buttons are **enabled** only when the current player can take an action on that player (based on game state and current role step)
    - Buttons are **disabled** when no action is available for that player
    - Player cards shown next to avatars (face-down during discussion, face-up when revealed by actions)
  - **Accrued Actions Display**: A persistent section listing all actions visible to the current player
    - Shows information learned during night phase (e.g., "You are a Werewolf. Your fellow werewolves are: [names]", "You viewed Alice's card. It is: SEER")
    - Actions persist and remain visible throughout the game (night phase through day phase)
    - Each action is displayed as a readable statement of what the player learned
- **Action Overlay (Per-Player Turn)**: When it is a player’s action time, show a full-screen overlay that contains instructions plus action UI
  - Overlay includes a list of player buttons and center card buttons as needed for the role action
  - If no action is required (e.g., multiple Werewolves), the overlay presents the information learned and requires the player to click "OK"
  - If an action is required, the overlay shows the result after the action is taken and requires "OK"
  - After dismissal, the result is persisted in the Accrued Actions Display
  - **Phase Indicator**: Shows current game state (Night, Day Discussion, Day Voting)
  - **Current Role Step**: When in NIGHT state, shows which role is currently active (`current_role_step` field)
  - **Game & Score Display**:
    - Current game number indicator (Game 1, Game 2, etc. within Game Set)
    - Cumulative score board (wins/losses per player across all games in Game Set) - visible during all phases
- **State-Based Behavior**:
  - **NIGHT State**: 
    - Screen adapts based on `current_role_step` field
    - Player buttons remain visible on the main screen
    - Center cards are not shown on the main screen (only shown in the action overlay when needed for night phase actions)
    - When it's a player's role turn: show the action overlay with instructions and role-specific buttons
    - When not their turn: all buttons disabled, shows "Waiting for [role] to complete action..."
    - Host (automated) calls each role in sequence (via text/audio)
  - **DAY_DISCUSSION State**:
    - All player buttons enabled (for discussion reference, but no actions available)
    - Center cards not shown on main screen (only shown in action overlay during night phase)
    - Timer countdown showing remaining discussion time
    - Chat actively used for discussion
    - Host automatically transitions to DAY_VOTING when timer expires
  - **DAY_VOTING State**:
    - All player buttons enabled (for voting - click to vote)
    - Center cards not shown on main screen (only shown in action overlay during night phase)
    - Vote confirmation dialog when clicking a player
    - Vote status display (who voted for whom, updated in real-time)
    - Chat disabled or restricted during voting
    - Host automatically advances to RESULTS when all votes cast
- **Action Enablement Logic**: Backend determines which buttons should be enabled based on:
  - Current game `state` (NIGHT, DAY_DISCUSSION, DAY_VOTING)
  - Current `current_role_step` (if state is NIGHT)
  - Player's current role
  - Whether player has already completed their required action
  - Endpoint: `GET /api/games/{game_id}/players/{player_id}/available-actions` returns which players/center cards are actionable

### 3. **Role Assignment UI**
- **Initial Role Reveal**: At start of game (before NIGHT phase), each player sees their own assigned role
  - Role card displayed with role name and instructions
  - Brief explanation of role abilities
  - Player acknowledges they've seen their role
- **Role Hidden After Reveal**: Once player acknowledges, their role card becomes hidden/face-down
  - Role may change during night phase (via actions), so it stays hidden
  - Player can only see their role again if their role allows viewing (e.g., Insomniac)
- **Center Cards**: Never revealed - remain secret throughout game (shown as face-down placeholders)

### 4. **Results Phase UI**
- **Results Screen**: 
  - Current game results:
    - Who died (if anyone)
    - Current role assignments (after all night actions)
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

### 5. **Frontend Component Architecture**

The unified game screen is built from modular components that handle different aspects of gameplay. Components are organized to support role-specific interactions and action types.

#### **Core Layout Components**
- **`GameBoard`** (`components/game/GameBoard.tsx`): Main container component that orchestrates the entire game screen
  - Manages game state polling and updates
  - Coordinates between overlay and main screen
  - Handles phase transitions
  - Renders appropriate components based on game state

- **`PlayerGrid`** (`components/game/PlayerGrid.tsx`): Displays all players as clickable buttons arranged around the board
  - Always visible on main screen
  - Receives click handler function as prop (handler varies by role/action type)
  - Handles enabled/disabled states based on available actions
  - Shows player avatars and names
  - Highlights current player

- **`AccruedActionsDisplay`** (`components/game/AccruedActionsDisplay.tsx`): Persistent section showing all actions visible to current player
  - Fetches from `GET /api/games/{game_id}/players/{player_id}/actions`
  - Displays each action as readable text
  - Persists throughout game (night through day)
  - Updates when new actions are recorded

- **`PhaseIndicator`** (`components/game/PhaseIndicator.tsx`): Shows current game phase
  - Displays: "Night Phase", "Day Discussion", "Day Voting", "Results"
  - Shows current role step during night phase
  - Visual indicator with phase-specific styling

#### **Action Overlay System**
- **`ActionOverlay`** (`components/game/actions/ActionOverlay.tsx`): Full-screen overlay container for night phase actions
  - Full-screen overlay that covers main game board
  - Contains role-specific action UI
  - Always requires "OK" button to dismiss
  - Manages overlay visibility state

- **`RoleActionHandler`** (`components/game/actions/RoleActionHandler.tsx`): Determines which role-specific action component to render
  - Receives current role and game state
  - Routes to appropriate role action component
  - Handles role detection logic

#### **Role-Specific Action Components** (in `components/game/actions/roles/`)
Each role has its own action component that handles role-specific interactions:

- **`WerewolfAction.tsx`**: Handles Werewolf turn
  - **Multiple werewolves**: Shows other werewolves list, requires acknowledgment
  - **Lone wolf**: Shows center card buttons, handles center card selection and viewing
  - Uses `PlayerButton` and `CenterCardButton` components within overlay

- **`SeerAction.tsx`**: Handles Seer turn (choice-based action)
  - Shows action type selection: "View one player" OR "View two center cards"
  - **If view player**: Renders `PlayerButton` components (excluding self)
  - **If view center**: Renders two `CenterCardButton` components (multi-select)
  - Displays results after selection

- **`RobberAction.tsx`**: Handles Robber turn (multi-step: swap + view)
  - Step 1: Shows `PlayerButton` components (excluding self) for selection
  - Step 2: After selection, shows result: "You robbed [player] and took their card. You are now: [NEW ROLE]"
  - Manages multi-step state

- **`TroublemakerAction.tsx`**: Handles Troublemaker turn (multi-select)
  - Shows `PlayerButton` components (excluding self)
  - Requires selecting TWO players
  - Tracks selection state (first player, second player)
  - Shows result after both selected: "You swapped [player1] and [player2]"

- **`DrunkAction.tsx`**: Handles Drunk turn
  - Shows `CenterCardButton` components
  - Single selection
  - Shows result: "You exchanged your card with center card [X]. You don't know your new role."

- **`InsomniacAction.tsx`**: Handles Insomniac turn (information display)
  - Shows current role after all night actions
  - Requires acknowledgment only
  - No button interactions needed

- **`MinionAction.tsx`**: Handles Minion turn (information display)
  - Shows werewolves list
  - Requires acknowledgment only
  - Similar to multiple werewolves flow

- **`MasonAction.tsx`**: Handles Mason turn (information display)
  - Shows other Mason (or indicates Mason is in center)
  - Requires acknowledgment only

#### **Interactive Button Components**
- **`PlayerButton`** (`components/game/PlayerButton.tsx`): Individual clickable player button
  - Receives click handler function as prop (handler varies by role)
  - Handles different action types:
    - **VIEW**: Click to view player's card (Seer)
    - **SWAP**: Click to swap with player (Robber)
    - **SELECT**: Click to select for multi-select actions (Troublemaker)
    - **VOTE**: Click to vote (Day Voting phase)
  - Shows enabled/disabled state
  - Displays player avatar, name, and role card (face-up/face-down)
  - Highlights when selected (for multi-select actions)

- **`CenterCardButton`** (`components/game/CenterCardButton.tsx`): Individual center card button
  - **Only shown in action overlay** (never on main screen)
  - Receives click handler function as prop
  - Handles different action types:
    - **VIEW**: Click to view center card (Lone Wolf, Seer viewing center)
    - **SWAP**: Click to swap with center card (Drunk)
  - Shows enabled/disabled state
  - Displays card index (0, 1, 2) or label (Left, Center, Right)
  - Highlights when selected

#### **Supporting Components**
- **`ChatComponent`** (`components/game/ChatComponent.tsx`): Persistent chat interface
  - Always visible on all screens and phases
  - Text chat (MVP)
  - Chat history persists throughout game session
  - Future: Audio/RTC support

- **`TimerDisplay`** (`components/game/TimerDisplay.tsx`): Countdown timer for discussion phase
  - Shows MM:SS format
  - Updates in real-time
  - Only visible during DAY_DISCUSSION phase

- **`VoteStatus`** (`components/game/VoteStatus.tsx`): Voting progress display
  - Shows "X/Y players have voted"
  - Shows who voted for whom (optional, may be hidden until all votes cast)
  - Only visible during DAY_VOTING phase

- **`ResultsDisplay`** (`components/game/ResultsDisplay.tsx`): Results screen
  - Shows vote counts, deaths, current roles
  - Shows team assignments and winners
  - "Play Another Game" and "End Game Set" buttons

- **`RoleReveal`** (`components/game/RoleReveal.tsx`): Initial role reveal screen
  - Shows role card with name and description
  - "I understand" acknowledgment button
  - Card flips face-down after acknowledgment

- **`LoadingSpinner`** (`components/shared/LoadingSpinner.tsx`): Loading state indicator
- **`ErrorDisplay`** (`components/shared/ErrorDisplay.tsx`): Error message display
- **`Toast`** (`components/shared/Toast.tsx`): Toast notifications for game events

#### **Component Interaction Patterns**

**Click Handler Strategy:**
- `PlayerButton` and `CenterCardButton` receive click handlers as props
- Click handlers are created by role-specific action components
- Handler function signature: `(targetId: string) => void` or `(cardIndex: number) => void`
- Different roles pass different handlers:
  - Seer viewing player: `(playerId) => viewPlayerCard(playerId)`
  - Robber: `(playerId) => swapWithPlayer(playerId)`
  - Troublemaker: `(playerId) => selectPlayerForSwap(playerId)` (tracks selection state)
  - Voting: `(playerId) => voteForPlayer(playerId)`

**Action Flow Pattern:**
1. Game state changes → `GameBoard` detects role turn
2. `GameBoard` renders `ActionOverlay` with `RoleActionHandler`
3. `RoleActionHandler` routes to appropriate role action component
4. Role action component renders `PlayerButton`/`CenterCardButton` with role-specific handlers
5. User clicks button → handler executes → API call → result displayed
6. User clicks "OK" → overlay dismisses → action persists in `AccruedActionsDisplay`

**State Management:**
- Game state (game, players, night status) managed in `GameBoard` via polling/WebSocket
- Action state (selections, results) managed in individual role action components
- Accrued actions fetched separately and displayed in `AccruedActionsDisplay`

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
- **Unified Screen State Management**: 
  - Screen adapts based on game `state` (NIGHT, DAY_DISCUSSION, DAY_VOTING, RESULTS) and `current_role_step` (when in NIGHT)
  - `GET /api/games/{game_id}/players/{player_id}/available-actions` - Returns which players/center cards are actionable for the current player
    - Response includes: `{ "actionable_players": [...], "actionable_center_cards": [...], "instructions": "..." }`
  - `GET /api/games/{game_id}/players/{player_id}/actions` - Returns all accrued actions visible to the player
    - Response includes list of action records that should be displayed persistently
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
  - Updates `current_role_step` field in Game table to track which role is active
  - **Information Display Roles** (automatic, no action required):
    - **Werewolves** (multiple - 2+): System automatically displays to all werewolves who the other werewolves are
    - **Minion**: System automatically displays to minion who all the werewolves are
    - **Masons**: System automatically displays to masons who the other mason is (or that other mason is in center)
    - These roles complete immediately (no waiting for player action - the indicators remain on their screen throughout the game)
    - Actions are recorded in Action table and displayed in accrued actions section
  - **Action Required Roles**:
    - **Werewolf (Lone Wolf - only 1 werewolf)**: Must choose which center card to view (player's choice, action required)
    - **Seer**: View one player card OR 2 center cards (no moving)
    - **Robber**: Exchange card with player AND view new card
    - **Troublemaker**: Exchange two other players' cards (no viewing)
    - **Drunk**: Exchange with center card (no viewing)
    - **Insomniac**: View own current card
  - **Action Validation**: Ensure actions are valid (correct targets, no duplicates)
  - **Action Completion Tracking**: Track which players have completed required actions (backend only - never exposed to frontend)
  - **Role Completion Status**: Aggregate player completions into role-based status (e.g., "Seer has acted") for host progression
  - **Host Progression**: Host automatically advances to next role when current role completes (immediate for info roles, after action for action roles)
  - **State Updates**: Apply actions to game state (card exchanges, views), update `current_role_step` as roles complete
- **Day Phase Manager**:
  - **Discussion Phase** (state = DAY_DISCUSSION):
    - Timer countdown (time limit set during game creation)
    - Chat enabled for discussion
    - All player buttons visible but no actions available (for reference only)
    - Host automatically transitions to Voting when timer expires (updates state to DAY_VOTING)
  - **Voting Phase** (state = DAY_VOTING):
    - **Voting System**:
      - `POST /api/games/{game_id}/vote` - Submit vote (clicking enabled player button)
      - `GET /api/games/{game_id}/votes` - Get current votes
    - Chat disabled/restricted during voting (no discussion)
    - All player buttons enabled (for voting)
    - All players vote simultaneously
    - **Vote Counting**: Determine who dies (tie resolution)
    - **Host Progression**: Host automatically advances to Results when all votes cast (updates state to RESULTS)

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

### 0. **Role Definitions** (Reference data for all roles)
- **Roles Table**:
  - `role_id` (String, primary key: role name, e.g., "Werewolf", "Seer", "Villager")
  - `has_action` (Boolean: whether this role wakes up during night phase)
  - `wake_order` (Integer, nullable: position in night wake sequence, null if has_action=false)
  - `team` (String: "village", "werewolf", or "tanner")
  - `description` (String, nullable: role description for UI display)
- **Available Roles**: Werewolf, Villager, Seer, Robber, Troublemaker, Minion, Mason, Drunk, Insomniac, Tanner, Hunter (refer to instructions.md)
- **Benefits**: Centralizes role metadata, enables querying by properties (e.g., "all roles that wake up"), ensures data integrity via foreign keys, and makes it easy to add new roles or properties without code changes

### 1. **Game Set Storage** (Groups multiple games together)
- **Game Set Table**:
  - `game_set_id` (UUID, primary key)
  - `created_by` (user/session ID of game set creator)
  - `num_players` (integer: number of players in this set)
  - `selected_roles` (JSON: array of role_id values selected for games in this set, references roles.role_id)
  - `discussion_timer_seconds` (integer: discussion time limit)
  - `created_at`, `updated_at`
  - `ended_at` (timestamp: when game set ended, null if active)

### 2. **Game State Storage** (Each game is a single round)
- **Game Table**:
  - `game_id` (UUID, primary key)
  - `game_set_id` (foreign key: which game set this game belongs to)
  - `game_number` (integer: sequence number within game set, 1, 2, 3, etc.)
  - `state` (enum: NIGHT, DAY_DISCUSSION, DAY_VOTING, RESULTS)
  - `current_role_step` (String, foreign key to roles.role_id: which role in the night sequence is currently active - only set when state is NIGHT)
  - `active_roles` (JSON: array of role_id strings) - Ordered list of active roles (roles with wake_order) present in this game (from both player roles and center cards), ordered by wake_order from the roles table. Created when all players have been assigned roles. Only includes roles that wake up at night (has_action=true). This provides a canonical ordering of active roles for the game.
  - `card_0_role` (String, foreign key to roles.role_id: role of center card at index 0 - kept secret, never exposed to players, updated when actions occur)
  - `card_1_role` (String, foreign key to roles.role_id: role of center card at index 1 - kept secret, never exposed to players, updated when actions occur)
  - `card_2_role` (String, foreign key to roles.role_id: role of center card at index 2 - kept secret, never exposed to players, updated when actions occur)
  - `created_at`, `updated_at`
  - `ended_at` (timestamp: when game ended)
- **Note**: When an action occurs (e.g., Drunk exchanges with center card), update the corresponding `card_X_role` field to reflect the new card in that center position. These fields always represent the current state of the 3 center positions. Center card roles are never revealed to players (only used internally for night actions like Seer viewing or Drunk exchanging).

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
  - `initial_role` (String, foreign key to roles.role_id: initial role assignment - only visible to that player)
  - `current_role` (String, foreign key to roles.role_id: current role after night actions - can change during night phase)
  - `role_revealed` (boolean: whether player has seen their initial role)
  - `team` (String: "village", "werewolf", or "tanner" - can be derived from role but cached for performance)
  - `was_killed` (boolean: whether player was killed at end of game)
  - `night_action_completed` (boolean: whether player has completed their night action/acknowledgment)
- **Note**: Player roles reference the roles table via foreign keys, ensuring data consistency. When a player's card is changed via an action, the `current_role` should be updated accordingly. The `team` field can be derived from the role's team property but is cached for query performance.

### 5. **Actions** (Night Phase Mutations)
- **Action Table**:
  - `action_id` (UUID, primary key)
  - `game_id` (foreign key: which game this action occurred in)
  - `player_id` (foreign key: which player performed the action)
  - `action_type` (enum: SWAP_PLAYER_TO_PLAYER, SWAP_PLAYER_TO_CENTER, VIEW_CARD)
  - `source_id` (string: player_id if source is a player, or "0"/"1"/"2" if source is a center card)
  - `target_id` (string: player_id if target is a player, or "0"/"1"/"2" if target is a center card, or "" if action_type is VIEW_CARD)
  - `source_role` (String, foreign key to roles.role_id: role of the source card)
  - `target_role` (String, foreign key to roles.role_id, nullable: role of the target card, or null if action_type is VIEW_CARD)
  - `timestamp`
- **Multiple Actions Per Player/Role**:
  - **Multiple Werewolves**: When there are 2+ werewolves, each werewolf gets a separate action record (VIEW_CARD type) showing they viewed the other werewolves. This ensures each werewolf has their action information persisted and displayed on their screen throughout the game.
  - **Seer Viewing Two Center Cards**: When the Seer chooses to view two center cards, create two separate action records (one per center card viewed). Both actions are persisted and displayed on the Seer's screen so they can reference both pieces of information.
  - **Masons**: Each Mason gets a separate action record (VIEW_CARD type) showing they viewed the other Mason (or that the other Mason is in the center). Both Masons have their action information persisted and displayed.
  - **Minion**: The Minion gets an action record (VIEW_CARD type) showing they viewed the werewolves (one action for each werewolf). This information persists on their screen.
  - **Note**: All action records are used to display persistent information on each player's screen during the night phase and into the day phase, allowing players to reference what they learned during their turn.

### 6. **Votes**
- **Vote Table**:
  - `vote_id` (UUID, primary key)
  - `game_id` (foreign key: which game this vote occurred in)
  - `voter_player_role_id` (player_role_id: who voted)
  - `target_player_role_id` (player_role_id: who was voted for)
  - `timestamp`

### 7. **Chat Messages** (Optional - can be ephemeral)
- **Chat Message Table**:
  - `message_id` (UUID, primary key)
  - `game_set_id` (foreign key: chat persists across games in a set)
  - `player_id` (who sent message)
  - `message` (text content)
  - `timestamp`

### 8. **Score Calculation** (Computed on-demand, no separate table)
- **Cumulative scores computed from existing tables**:
  - Query Player Role table for all games in a Game Set
  - Join with Votes table to determine who died in each game
  - Apply win condition logic to determine winners for each game
  - Check if each player's team won (based on current_role, team, was_killed, and deaths)
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
4. **Role Changes**: Tracking role changes through gameplay night phase via actions
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
