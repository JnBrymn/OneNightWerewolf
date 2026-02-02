# One Night Werewolf - Implementation Steps

## Overview
This document breaks down the implementation into demonstrable milestones. Each step includes:
- **Backend**: Testable API endpoints with curl examples
- **Frontend**: Visible UI components
- **Tests**: Written BEFORE implementation (TDD) - both backend AND frontend
- **Demo**: Clear way to verify the step works

---

## Testing Strategy

### Backend Testing (Python/Pytest)
- **What to test**: API endpoints, business logic, database operations
- **Tools**: pytest, FastAPI TestClient
- **Focus**: HTTP responses, validation, database state
- **Example**: Test that POST /api/players creates a player

### Frontend Testing (Jest + React Testing Library)
- **What to test**: User interactions, navigation, form validation, API integration
- **Tools**: Jest (test runner), React Testing Library (component testing)
- **Focus**: What users see and do, NOT implementation details
- **What NOT to test**: Styling, CSS, internal state, third-party libraries

### Frontend Test Examples:
```javascript
// Good: Test user behavior
test('clicking Create Game navigates to /create', () => {
  render(<Home />)
  const button = screen.getByText('Create Game')
  fireEvent.click(button)
  expect(mockRouter.push).toHaveBeenCalledWith('/create')
})

// Good: Test form validation
test('shows error when role count is wrong', () => {
  render(<CreateGame />)
  // ... submit with wrong role count
  expect(screen.getByText(/must equal players/)).toBeInTheDocument()
})

// Bad: Don't test implementation details
test('useState hook has correct initial value', () => { ... }) // ❌
```

---

## Step 1: Project Setup & Basic Infrastructure

### Backend Tasks
1. **Setup FastAPI project structure**
   - Install dependencies: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `pytest`
   - Create basic app structure (`main.py`, `models/`, `api/`, `tests/`)
   - Setup SQLite database connection
   - Create health check endpoint

2. **Write Tests First** (`tests/test_health.py`)
   ```python
   def test_health_check():
       response = client.get("/health")
       assert response.status_code == 200
       assert response.json() == {"status": "healthy"}
   ```

3. **Implement health check endpoint**

### Frontend Tasks
1. **Setup Next.js project**
   - Create Next.js app with App Router
   - Install dependencies: `zustand`, `tailwindcss`
   - Setup test environment: `jest`, `@testing-library/react`, `@testing-library/jest-dom`
   - Setup basic layout and homepage

2. **Write Tests First** (`__tests__/landing.test.tsx`)
   ```javascript
   test('renders landing page with title', () => {
     render(<Home />)
     expect(screen.getByText('One Night Werewolf')).toBeInTheDocument()
   })

   test('has Create Game and Join Game buttons', () => {
     render(<Home />)
     expect(screen.getByText('Create Game')).toBeInTheDocument()
     expect(screen.getByText('Join Game')).toBeInTheDocument()
   })
   ```

3. **Create basic landing page**
   - Simple welcome screen
   - "Create Game" and "Join Game" buttons (navigation in Step 2)

### Demo
**Backend:**
```bash
# Start server
uvicorn main:app --reload

# Health check
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

**Frontend:**
```bash
# Start dev server
npm run dev

# Visit http://localhost:3000
# See: Landing page with two buttons
```

---

## Step 2: Game Set Creation (Lobby Start)

### Backend Tasks
1. **Write Tests First** (`tests/test_game_sets.py`)
   ```python
   def test_create_game_set():
       response = client.post("/api/game-sets", json={
           "num_players": 5,
           "selected_roles": ["Werewolf", "Werewolf", "Villager", "Villager", "Villager", "Seer", "Robber", "Troublemaker"],
           "discussion_timer_seconds": 300
       })
       assert response.status_code == 201
       assert "game_set_id" in response.json()
       assert response.json()["num_players"] == 5

   def test_get_game_set():
       # Create game set first
       create_response = client.post("/api/game-sets", ...)
       game_set_id = create_response.json()["game_set_id"]

       # Get game set
       response = client.get(f"/api/game-sets/{game_set_id}")
       assert response.status_code == 200
       assert response.json()["num_players"] == 5
   ```

2. **Create database models**
   - `GameSet` model with fields from schema
   - Database migrations/initialization

3. **Implement endpoints**
   - `POST /api/game-sets` - Create game set
   - `GET /api/game-sets/{game_set_id}` - Get game set details

### Frontend Tasks
1. **Create Game Setup Page** (`/create`)
   - Form for number of players (3-10)
   - Role selection checkboxes (ensure cards = players + 3)
   - Discussion timer input (default 300 seconds)
   - Submit button

2. **Connect to API**
   - Call `POST /api/game-sets` on form submit
   - Redirect to lobby page with game_set_id

### Demo
**Backend:**
```bash
# Create game set
curl -X POST http://localhost:8000/api/game-sets \
  -H "Content-Type: application/json" \
  -d '{
    "num_players": 5,
    "selected_roles": ["Werewolf", "Werewolf", "Villager", "Villager", "Villager", "Seer", "Robber", "Troublemaker"],
    "discussion_timer_seconds": 300
  }'
# Expected: {"game_set_id": "...", "num_players": 5, ...}

# Get game set
curl http://localhost:8000/api/game-sets/{game_set_id}
# Expected: Full game set details
```

**Frontend:**
- Visit `/create`
- Fill form (5 players, select 8 roles)
- Click "Create Game"
- See redirect to lobby page (URL shows game_set_id)

---

## Step 3: Player Management & Lobby

### Backend Tasks
1. **Write Tests First** (`tests/test_players.py`)
   ```python
   def test_create_player():
       response = client.post("/api/players", json={
           "player_name": "Alice",
           "avatar_url": "https://example.com/avatar.jpg"
       })
       assert response.status_code == 201
       assert "player_id" in response.json()
       assert response.json()["player_name"] == "Alice"

   def test_join_game_set():
       # Create game set and player first
       game_set_id = ...
       player_id = ...

       response = client.post(f"/api/game-sets/{game_set_id}/players/{player_id}/join")
       assert response.status_code == 200

   def test_list_players_in_game_set():
       response = client.get(f"/api/game-sets/{game_set_id}/players")
       assert response.status_code == 200
       assert len(response.json()["players"]) == 1
       assert response.json()["players"][0]["player_name"] == "Alice"

   def test_cannot_start_game_without_enough_players():
       # Game set needs 5 players, only 2 joined
       response = client.post(f"/api/game-sets/{game_set_id}/start")
       assert response.status_code == 400
   ```

2. **Create database models**
   - `Player` model
   - `GameSetPlayer` join table (many-to-many)

3. **Implement endpoints**
   - `POST /api/players` - Create player
   - `POST /api/game-sets/{game_set_id}/players/{player_id}/join` - Join game set
   - `GET /api/game-sets/{game_set_id}/players` - List players
   - `POST /api/game-sets/{game_set_id}/start` - Start game (validates player count)

### Frontend Tasks
1. **Create Join Game Page** (`/join`)
   - Input for game set code/ID
   - Input for player name
   - Optional avatar upload/URL
   - Join button

2. **Create Lobby Page** (`/game/[game_set_id]`)
   - Show game set details (num players needed, selected roles)
   - List of joined players with avatars
   - "Start Game" button (enabled when enough players joined)
   - Display "Waiting for players..." count

3. **Add basic polling**
   - Poll `/api/game-sets/{game_set_id}/players` every 2 seconds
   - Update player list in real-time

### Demo
**Backend:**
```bash
# Create player
curl -X POST http://localhost:8000/api/players \
  -H "Content-Type: application/json" \
  -d '{"player_name": "Alice"}'
# Expected: {"player_id": "...", "player_name": "Alice"}

# Join game set
curl -X POST http://localhost:8000/api/game-sets/{game_set_id}/players/{player_id}/join
# Expected: {"status": "joined"}

# List players
curl http://localhost:8000/api/game-sets/{game_set_id}/players
# Expected: {"players": [{"player_id": "...", "player_name": "Alice"}]}

# Try to start (should fail - not enough players)
curl -X POST http://localhost:8000/api/game-sets/{game_set_id}/start
# Expected: 400 error

# Add 4 more players, then start (should succeed)
curl -X POST http://localhost:8000/api/game-sets/{game_set_id}/start
# Expected: {"game_id": "...", "state": "NIGHT"}
```

**Frontend:**
- Open `/create` in browser 1, create 5-player game
- Copy game_set_id from URL
- Open `/join` in browsers 2-6 (simulate 5 players)
- Enter game_set_id and player names
- See lobby page populate with players
- In browser 1, see "Start Game" button enable when 5 players joined
- Click "Start Game"

---

## Step 4: Game Creation & Role Assignment

### Backend Tasks
1. **Write Tests First** (`tests/test_game_creation.py`)
   ```python
   def test_create_game_in_set():
       # Setup: Create game set with 5 players
       game_set_id = ...

       response = client.post(f"/api/game-sets/{game_set_id}/start")
       assert response.status_code == 201
       assert "game_id" in response.json()
       assert response.json()["state"] == "NIGHT"
       assert response.json()["game_number"] == 1

   def test_role_assignment():
       game_id = ...

       # Get all player roles
       response = client.get(f"/api/games/{game_id}/player-roles")
       assert response.status_code == 200
       player_roles = response.json()["player_roles"]

       # Should have 5 player roles assigned
       assert len(player_roles) == 5

       # All roles should be from selected role collection
       assigned_roles = [pr["initial_role"] for pr in player_roles]
       assert all(role in SELECTED_ROLES for role in assigned_roles)

   def test_center_cards_created():
       game_id = ...

       # Center cards should exist (internal check)
       response = client.get(f"/api/games/{game_id}/center-cards")
       assert response.status_code == 200
       assert len(response.json()["center_cards"]) == 3

       # Center cards should NOT be visible to players
       # This endpoint should be admin/test-only

   def test_player_can_see_own_role():
       game_id = ...
       player_id = ...

       response = client.get(f"/api/games/{game_id}/players/{player_id}/role")
       assert response.status_code == 200
       assert "initial_role" in response.json()
       assert response.json()["initial_role"] in SELECTED_ROLES

   def test_player_cannot_see_other_roles():
       game_id = ...
       player1_id = ...
       player2_id = ...

       # Player 1 tries to get Player 2's role
       response = client.get(
           f"/api/games/{game_id}/players/{player2_id}/role",
           headers={"X-Player-ID": player1_id}  # Auth header
       )
       assert response.status_code == 403
   ```

2. **Create database models**
   - `Game` model
   - `PlayerRole` model
   - `CenterCard` model

3. **Implement role assignment logic**
   - Shuffle and assign roles from selected collection
   - Assign N cards to players, 3 to center
   - Store initial roles in database

4. **Implement endpoints**
   - `POST /api/game-sets/{game_set_id}/start` - Create first game, assign roles
   - `GET /api/games/{game_id}` - Get game state
   - `GET /api/games/{game_id}/players/{player_id}/role` - Get player's own role (auth required)

### Frontend Tasks
1. **Update Lobby Page**
   - When "Start Game" clicked, call API
   - Redirect all players to game page

2. **Create Role Reveal Screen** (`/game/[game_set_id]` when state = NIGHT and role not revealed)
   - Show "Your role is:" with role card
   - Display role name and description
   - "I understand" acknowledgment button
   - After acknowledgment, card flips face-down

3. **Add session management**
   - Store player_id in localStorage/cookie
   - Use for authentication in API calls

### Demo
**Backend:**
```bash
# Start game (creates first game in set)
curl -X POST http://localhost:8000/api/game-sets/{game_set_id}/start
# Expected: {"game_id": "...", "state": "NIGHT", "game_number": 1}

# Get game state
curl http://localhost:8000/api/games/{game_id}
# Expected: Game details with state="NIGHT"

# Get player's role (as player 1)
curl http://localhost:8000/api/games/{game_id}/players/{player1_id}/role \
  -H "X-Player-ID: {player1_id}"
# Expected: {"initial_role": "Werewolf", "role_revealed": false}

# Try to get another player's role (should fail)
curl http://localhost:8000/api/games/{game_id}/players/{player2_id}/role \
  -H "X-Player-ID: {player1_id}"
# Expected: 403 Forbidden
```

**Frontend:**
- In lobby, click "Start Game"
- See role reveal screen with your assigned role
- Click "I understand"
- See card flip face-down
- (Stop here - Night phase UI comes next)

---

## Step 5: Night Phase - Basic Infrastructure

### Backend Tasks
1. **Write Tests First** (`tests/test_night_phase.py`)
   ```python
   def test_night_phase_wake_order():
       game_id = ...

       # Get current night phase status
       response = client.get(f"/api/games/{game_id}/night-status")
       assert response.status_code == 200
       assert response.json()["current_role"] == "Werewolf"  # First role
       assert response.json()["roles_completed"] == []

   def test_mark_role_complete():
       game_id = ...

       # Mark Werewolf phase complete
       response = client.post(f"/api/games/{game_id}/night-status/complete", json={
           "role": "Werewolf"
       })
       assert response.status_code == 200

       # Check updated status
       response = client.get(f"/api/games/{game_id}/night-status")
       assert "Werewolf" in response.json()["roles_completed"]
       assert response.json()["current_role"] == "Minion"  # Next in sequence

   def test_night_phase_ends_after_all_roles():
       game_id = ...

       # Complete all roles in sequence
       for role in NIGHT_WAKE_ORDER:
           client.post(f"/api/games/{game_id}/night-status/complete", json={"role": role})

       # Game should transition to DAY_DISCUSSION
       response = client.get(f"/api/games/{game_id}")
       assert response.json()["state"] == "DAY_DISCUSSION"
   ```

2. **Implement night phase orchestration**
   - Night wake order manager
   - Track current role in sequence
   - Track completed roles
   - Auto-advance to next role when current completes
   - Transition to DAY_DISCUSSION when all roles complete

3. **Implement endpoints**
   - `GET /api/games/{game_id}/night-status` - Get current night phase status
   - `POST /api/games/{game_id}/night-status/complete` - Mark role complete

### Frontend Tasks
1. **Create Night Phase UI** (`/game/[game_set_id]` when state = NIGHT)
   - Show "Night Phase" header
   - Display current role being called (for all players)
   - "Waiting for {role} to complete action..." message
   - Simple loading spinner

2. **Add polling for night status**
   - Poll `/api/games/{game_id}/night-status` every 2 seconds
   - Update UI when current role changes

### Demo
**Backend:**
```bash
# Get night status
curl http://localhost:8000/api/games/{game_id}/night-status
# Expected: {"current_role": "Werewolf", "roles_completed": []}

# Mark Werewolf complete
curl -X POST http://localhost:8000/api/games/{game_id}/night-status/complete \
  -H "Content-Type: application/json" \
  -d '{"role": "Werewolf"}'
# Expected: {"status": "ok", "next_role": "Minion"}

# Check status again
curl http://localhost:8000/api/games/{game_id}/night-status
# Expected: {"current_role": "Minion", "roles_completed": ["Werewolf"]}
```

**Frontend:**
- After role reveal, see Night Phase screen
- See "Night Phase - Werewolf is acting..."
- (Werewolves see their turn UI - implemented in next step)
- After Werewolf completes, see "Night Phase - Minion is acting..."

---

## Step 6: Night Phase - Werewolf Role (Information Display)

### Backend Tasks
1. **Write Tests First** (`tests/test_werewolf_role.py`)
   ```python
   def test_werewolf_sees_other_werewolves():
       # Setup: Create game with 2+ Werewolves
       game_id = ...
       werewolf1_id = ...

       response = client.get(
           f"/api/games/{game_id}/players/{werewolf1_id}/night-info",
           headers={"X-Player-ID": werewolf1_id}
       )
       assert response.status_code == 200
       assert response.json()["role"] == "Werewolf"
       assert "other_werewolves" in response.json()
       assert len(response.json()["other_werewolves"]) >= 1

   def test_lone_wolf_can_view_center():
       # Setup: Create game with only 1 Werewolf
       game_id = ...
       werewolf_id = ...

       # Werewolf chooses to view center card 0
       response = client.post(
           f"/api/games/{game_id}/players/{werewolf_id}/view-center",
           json={"card_index": 0},
           headers={"X-Player-ID": werewolf_id}
       )
       assert response.status_code == 200
       assert "role" in response.json()  # Shows center card role

   def test_werewolf_action_auto_completes():
       # Multiple werewolves: auto-complete when last werewolf acknowledges
       # Lone wolf: completes when center card viewed
       game_id = ...

       # All werewolves acknowledge
       for werewolf_id in werewolf_ids:
           client.post(
               f"/api/games/{game_id}/players/{werewolf_id}/acknowledge",
               headers={"X-Player-ID": werewolf_id}
           )

       # Check that Werewolf phase is complete
       response = client.get(f"/api/games/{game_id}/night-status")
       assert "Werewolf" in response.json()["roles_completed"]

   def test_non_werewolf_cannot_access_werewolf_info():
       game_id = ...
       seer_id = ...  # Player who is NOT a werewolf

       response = client.get(
           f"/api/games/{game_id}/players/{seer_id}/night-info",
           headers={"X-Player-ID": seer_id}
       )
       assert response.status_code == 200
       assert response.json()["role"] == "Seer"
       assert "other_werewolves" not in response.json()
   ```

2. **Implement werewolf logic**
   - Identify all werewolves in game
   - If 2+ werewolves: automatically show each werewolf the others
   - If 1 werewolf (lone wolf): allow viewing 1 center card
   - Track werewolf acknowledgments
   - Auto-complete when all werewolves acknowledge (or lone wolf views card)

3. **Implement endpoints**
   - `GET /api/games/{game_id}/players/{player_id}/night-info` - Get role-specific info
   - `POST /api/games/{game_id}/players/{player_id}/view-center` - View center card (lone wolf only)
   - `POST /api/games/{game_id}/players/{player_id}/acknowledge` - Acknowledge seeing info

### Frontend Tasks
1. **Create Werewolf Turn UI**
   - When it's Werewolf turn AND player is a werewolf:
     - **Multiple werewolves**: Show "You are a Werewolf. Your fellow werewolves are: [names]"
     - **Lone wolf**: Show "You are the lone werewolf. Choose a center card to view: [Card 1] [Card 2] [Card 3]"
   - "Continue" button to acknowledge

2. **Create Waiting UI**
   - When it's Werewolf turn but player is NOT a werewolf:
     - Show "Waiting for Werewolves to complete their turn..."

### Demo
**Backend:**
```bash
# Get night info (as Werewolf player)
curl http://localhost:8000/api/games/{game_id}/players/{werewolf1_id}/night-info \
  -H "X-Player-ID: {werewolf1_id}"
# Expected: {"role": "Werewolf", "other_werewolves": [{"player_id": "...", "player_name": "Bob"}]}

# Lone wolf views center card
curl -X POST http://localhost:8000/api/games/{game_id}/players/{werewolf_id}/view-center \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: {werewolf_id}" \
  -d '{"card_index": 1}'
# Expected: {"role": "Villager"}

# Acknowledge (for each werewolf)
curl -X POST http://localhost:8000/api/games/{game_id}/players/{werewolf1_id}/acknowledge \
  -H "X-Player-ID: {werewolf1_id}"
# Expected: {"status": "ok"}

# After all werewolves acknowledge, check night status
curl http://localhost:8000/api/games/{game_id}/night-status
# Expected: {"current_role": "Minion", "roles_completed": ["Werewolf"]}
```

**Frontend:**
- Werewolf player sees: "You are a Werewolf. Your fellow werewolves are: [Bob, Charlie]"
- Click "Continue"
- See "Waiting for Minion to complete their turn..."
- Non-werewolf players see: "Waiting for Werewolves..."

---

## Step 7: Night Phase - Seer Role (Action with Choice)

### Backend Tasks
1. **Write Tests First** (`tests/test_seer_role.py`)
   ```python
   def test_seer_can_view_one_player():
       game_id = ...
       seer_id = ...
       target_player_id = ...

       response = client.post(
           f"/api/games/{game_id}/players/{seer_id}/seer-action",
           json={"action_type": "view_player", "target_player_id": target_player_id},
           headers={"X-Player-ID": seer_id}
       )
       assert response.status_code == 200
       assert "role" in response.json()  # Shows target's role

   def test_seer_can_view_two_center_cards():
       game_id = ...
       seer_id = ...

       response = client.post(
           f"/api/games/{game_id}/players/{seer_id}/seer-action",
           json={"action_type": "view_center", "card_indices": [0, 1]},
           headers={"X-Player-ID": seer_id}
       )
       assert response.status_code == 200
       assert len(response.json()["roles"]) == 2

   def test_seer_cannot_view_three_center_cards():
       game_id = ...
       seer_id = ...

       response = client.post(
           f"/api/games/{game_id}/players/{seer_id}/seer-action",
           json={"action_type": "view_center", "card_indices": [0, 1, 2]},
           headers={"X-Player-ID": seer_id}
       )
       assert response.status_code == 400

   def test_seer_action_marks_role_complete():
       game_id = ...
       seer_id = ...

       # Perform seer action
       client.post(
           f"/api/games/{game_id}/players/{seer_id}/seer-action",
           json={"action_type": "view_player", "target_player_id": "..."},
           headers={"X-Player-ID": seer_id}
       )

       # Check that Seer is complete (if only one Seer in game)
       response = client.get(f"/api/games/{game_id}/night-status")
       assert "Seer" in response.json()["roles_completed"]

   def test_non_seer_cannot_perform_seer_action():
       game_id = ...
       werewolf_id = ...  # Player who is NOT the Seer

       response = client.post(
           f"/api/games/{game_id}/players/{werewolf_id}/seer-action",
           json={"action_type": "view_player", "target_player_id": "..."},
           headers={"X-Player-ID": werewolf_id}
       )
       assert response.status_code == 403
   ```

2. **Implement Seer logic**
   - Validate player is Seer
   - Handle two action types: view player OR view 2 center cards
   - Return viewed role(s)
   - Mark Seer role complete when action performed

3. **Implement endpoints**
   - `POST /api/games/{game_id}/players/{player_id}/seer-action` - Perform Seer action

### Frontend Tasks
1. **Create Seer Turn UI**
   - When it's Seer turn AND player is Seer:
     - Show two options: "View one player's card" or "View two center cards"
     - If "View player": Show clickable player avatars (excluding self)
     - If "View center": Show two center card selectors
     - After selection, show revealed role(s)
     - "Continue" button after viewing

2. **Show game board with selectable elements**
   - Player cards around board (clickable when Seer is choosing)
   - Center cards (clickable when Seer is choosing)

### Demo
**Backend:**
```bash
# Seer views one player
curl -X POST http://localhost:8000/api/games/{game_id}/players/{seer_id}/seer-action \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: {seer_id}" \
  -d '{"action_type": "view_player", "target_player_id": "{target_id}"}'
# Expected: {"role": "Robber"}

# Seer views two center cards
curl -X POST http://localhost:8000/api/games/{game_id}/players/{seer_id}/seer-action \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: {seer_id}" \
  -d '{"action_type": "view_center", "card_indices": [0, 2]}'
# Expected: {"roles": ["Villager", "Troublemaker"]}

# Check night status
curl http://localhost:8000/api/games/{game_id}/night-status
# Expected: {"current_role": "Robber", "roles_completed": ["Werewolf", "Minion", "Seer"]}
```

**Frontend:**
- Seer sees: "Choose your action: [View Player] [View Center Cards]"
- Click "View Player"
- Player avatars become clickable
- Click on Bob's avatar
- See: "Bob's card is: ROBBER"
- Click "Continue"
- See waiting screen for next role

---

## Step 8: Night Phase - Robber Role (Swap with View)

### Backend Tasks
1. **Write Tests First** (`tests/test_robber_role.py`)
   ```python
   def test_robber_swaps_and_views():
       game_id = ...
       robber_id = ...
       target_id = ...

       # Get original roles
       robber_original = get_player_role(game_id, robber_id)
       target_original = get_player_role(game_id, target_id)

       assert robber_original["initial_role"] == "Robber"

       # Robber swaps with target
       response = client.post(
           f"/api/games/{game_id}/players/{robber_id}/robber-action",
           json={"target_player_id": target_id},
           headers={"X-Player-ID": robber_id}
       )
       assert response.status_code == 200
       assert "new_role" in response.json()

       # Verify swap occurred
       robber_after = get_player_role(game_id, robber_id)
       target_after = get_player_role(game_id, target_id)

       assert robber_after["current_role"] == target_original["initial_role"]
       assert target_after["current_role"] == "Robber"

   def test_robber_creates_swap_record():
       game_id = ...
       robber_id = ...
       target_id = ...

       # Perform swap
       client.post(
           f"/api/games/{game_id}/players/{robber_id}/robber-action",
           json={"target_player_id": target_id},
           headers={"X-Player-ID": robber_id}
       )

       # Check swap was recorded
       swaps = get_game_swaps(game_id)
       assert len(swaps) == 1
       assert swaps[0]["swap_type"] == "PLAYER_TO_PLAYER"
       assert swaps[0]["source_player_id"] == robber_id
       assert swaps[0]["target_player_id"] == target_id

   def test_robber_cannot_swap_with_self():
       game_id = ...
       robber_id = ...

       response = client.post(
           f"/api/games/{game_id}/players/{robber_id}/robber-action",
           json={"target_player_id": robber_id},
           headers={"X-Player-ID": robber_id}
       )
       assert response.status_code == 400
   ```

2. **Implement Robber logic**
   - Validate player is Robber
   - Swap roles between Robber and target player
   - Return new role to Robber (for viewing)
   - Create swap record in database
   - Mark Robber role complete

3. **Implement endpoints**
   - `POST /api/games/{game_id}/players/{player_id}/robber-action` - Swap and view

### Frontend Tasks
1. **Create Robber Turn UI**
   - When it's Robber turn AND player is Robber:
     - Show: "Choose a player to rob (swap cards with)"
     - Display clickable player avatars (excluding self)
     - After selection: "You robbed [player] and became: [NEW ROLE]"
     - "Continue" button

### Demo
**Backend:**
```bash
# Robber swaps with target
curl -X POST http://localhost:8000/api/games/{game_id}/players/{robber_id}/robber-action \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: {robber_id}" \
  -d '{"target_player_id": "{target_id}"}'
# Expected: {"new_role": "Seer", "message": "You are now the Seer"}

# Verify swap in game state
curl http://localhost:8000/api/games/{game_id}/players/{robber_id}/role \
  -H "X-Player-ID: {robber_id}"
# Expected: {"current_role": "Seer"}
```

**Frontend:**
- Robber sees: "Choose a player to rob"
- Clicks on Alice's avatar
- See: "You robbed Alice and became: SEER"
- Click "Continue"

---

## Step 9: Night Phase - Troublemaker & Drunk (Blind Swaps)

### Backend Tasks
1. **Write Tests First** (`tests/test_troublemaker_drunk.py`)
   ```python
   def test_troublemaker_swaps_two_players():
       game_id = ...
       troublemaker_id = ...
       player1_id = ...
       player2_id = ...

       # Get original roles
       p1_original = get_player_role(game_id, player1_id)
       p2_original = get_player_role(game_id, player2_id)

       # Troublemaker swaps
       response = client.post(
           f"/api/games/{game_id}/players/{troublemaker_id}/troublemaker-action",
           json={"player1_id": player1_id, "player2_id": player2_id},
           headers={"X-Player-ID": troublemaker_id}
       )
       assert response.status_code == 200

       # Verify swap (roles exchanged)
       p1_after = get_player_role(game_id, player1_id)
       p2_after = get_player_role(game_id, player2_id)

       assert p1_after["current_role"] == p2_original["current_role"]
       assert p2_after["current_role"] == p1_original["current_role"]

   def test_drunk_swaps_with_center():
       game_id = ...
       drunk_id = ...

       # Get original role
       drunk_original = get_player_role(game_id, drunk_id)
       center_original = get_center_card(game_id, 1)

       # Drunk swaps with center card 1
       response = client.post(
           f"/api/games/{game_id}/players/{drunk_id}/drunk-action",
           json={"card_index": 1},
           headers={"X-Player-ID": drunk_id}
       )
       assert response.status_code == 200
       assert response.json()["message"] == "You exchanged your card with a center card"

       # Drunk doesn't see new role
       assert "new_role" not in response.json()

       # Verify swap occurred
       drunk_after = get_player_role(game_id, drunk_id)
       center_after = get_center_card(game_id, 1)

       assert drunk_after["current_role"] == center_original["role"]
       assert center_after["role"] == drunk_original["current_role"]
   ```

2. **Implement Troublemaker & Drunk logic**
   - Troublemaker: Swap two other players (no viewing)
   - Drunk: Swap with center card (no viewing)
   - Create swap records
   - Mark roles complete

3. **Implement endpoints**
   - `POST /api/games/{game_id}/players/{player_id}/troublemaker-action`
   - `POST /api/games/{game_id}/players/{player_id}/drunk-action`

### Frontend Tasks
1. **Create Troublemaker Turn UI**
   - Show: "Choose two players to swap"
   - Clickable player avatars (excluding self)
   - Select two players
   - Show: "You swapped [player1] and [player2]"
   - No role reveal

2. **Create Drunk Turn UI**
   - Show: "Choose a center card to swap with"
   - Three center card selectors
   - Click one
   - Show: "You exchanged your card with a center card. You don't know your new role."

### Demo
**Backend:**
```bash
# Troublemaker swaps two players
curl -X POST http://localhost:8000/api/games/{game_id}/players/{troublemaker_id}/troublemaker-action \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: {troublemaker_id}" \
  -d '{"player1_id": "{p1_id}", "player2_id": "{p2_id}"}'
# Expected: {"message": "Swapped two players"}

# Drunk swaps with center
curl -X POST http://localhost:8000/api/games/{game_id}/players/{drunk_id}/drunk-action \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: {drunk_id}" \
  -d '{"card_index": 2}'
# Expected: {"message": "You exchanged your card with a center card"}
```

**Frontend:**
- Troublemaker: Select Bob and Charlie, see "You swapped Bob and Charlie"
- Drunk: Click center card 2, see "You exchanged cards. You don't know your new role."

---

## Step 10: Night Phase - Insomniac (View After Swaps)

### Backend Tasks
1. **Write Tests First** (`tests/test_insomniac.py`)
   ```python
   def test_insomniac_sees_current_role():
       # Setup: Game where Insomniac was swapped by Troublemaker
       game_id = ...
       insomniac_id = ...

       # Insomniac's current role may differ from initial role
       response = client.get(
           f"/api/games/{game_id}/players/{insomniac_id}/insomniac-view",
           headers={"X-Player-ID": insomniac_id}
       )
       assert response.status_code == 200
       assert "current_role" in response.json()

   def test_insomniac_is_last_role():
       game_id = ...

       # After Insomniac completes, night ends
       insomniac_id = get_insomniac_player(game_id)

       client.post(
           f"/api/games/{game_id}/players/{insomniac_id}/acknowledge",
           headers={"X-Player-ID": insomniac_id}
       )

       # Game should transition to DAY_DISCUSSION
       response = client.get(f"/api/games/{game_id}")
       assert response.json()["state"] == "DAY_DISCUSSION"
   ```

2. **Implement Insomniac logic**
   - Show Insomniac their current role (after all swaps)
   - Mark Insomniac complete
   - Transition to DAY_DISCUSSION when complete

3. **Implement endpoints**
   - `GET /api/games/{game_id}/players/{player_id}/insomniac-view` - View current role

### Frontend Tasks
1. **Create Insomniac Turn UI**
   - Show: "You wake up and check your card"
   - Display current role (may be different from initial)
   - "Continue" button

### Demo
**Backend:**
```bash
# Insomniac views current role
curl http://localhost:8000/api/games/{game_id}/players/{insomniac_id}/insomniac-view \
  -H "X-Player-ID: {insomniac_id}"
# Expected: {"current_role": "Robber"}  # (was swapped during night)

# Acknowledge
curl -X POST http://localhost:8000/api/games/{game_id}/players/{insomniac_id}/acknowledge \
  -H "X-Player-ID: {insomniac_id}"

# Check game state
curl http://localhost:8000/api/games/{game_id}
# Expected: {"state": "DAY_DISCUSSION"}
```

**Frontend:**
- Insomniac sees: "You wake up. Your current role is: ROBBER"
- Click "Continue"
- Transition to Day Discussion phase

---

## Step 11: Day Discussion Phase

### Backend Tasks
1. **Write Tests First** (`tests/test_day_discussion.py`)
   ```python
   def test_discussion_timer_starts():
       game_id = ...

       # Game just transitioned to DAY_DISCUSSION
       response = client.get(f"/api/games/{game_id}/discussion-status")
       assert response.status_code == 200
       assert response.json()["time_remaining_seconds"] > 0
       assert response.json()["time_remaining_seconds"] <= 300  # Max timer value

   def test_discussion_timer_countdown():
       game_id = ...

       # Get initial time
       r1 = client.get(f"/api/games/{game_id}/discussion-status")
       time1 = r1.json()["time_remaining_seconds"]

       # Wait 5 seconds
       import time
       time.sleep(5)

       # Get updated time
       r2 = client.get(f"/api/games/{game_id}/discussion-status")
       time2 = r2.json()["time_remaining_seconds"]

       assert time2 < time1
       assert time1 - time2 >= 4  # Approximately 5 seconds passed

   def test_auto_transition_to_voting():
       game_id = ...

       # Set short timer (5 seconds for testing)
       # Wait for timer to expire
       import time
       time.sleep(6)

       # Game should auto-transition to DAY_VOTING
       response = client.get(f"/api/games/{game_id}")
       assert response.json()["state"] == "DAY_VOTING"
   ```

2. **Implement discussion timer**
   - Start countdown when entering DAY_DISCUSSION
   - Track elapsed time
   - Auto-transition to DAY_VOTING when timer expires

3. **Implement endpoints**
   - `GET /api/games/{game_id}/discussion-status` - Get timer status

### Frontend Tasks
1. **Create Discussion Phase UI**
   - Show "Day Phase - Discussion" header
   - Display countdown timer (MM:SS format)
   - Show all players around game board
   - Chat box for discussion (prominent)
   - All cards face-down (no roles visible)

2. **Auto-transition when timer expires**
   - Poll discussion status
   - When time reaches 0, transition to Voting UI

### Demo
**Backend:**
```bash
# Get discussion status
curl http://localhost:8000/api/games/{game_id}/discussion-status
# Expected: {"time_remaining_seconds": 295, "state": "DAY_DISCUSSION"}

# Wait and check again
# (in 5 seconds)
curl http://localhost:8000/api/games/{game_id}/discussion-status
# Expected: {"time_remaining_seconds": 290, "state": "DAY_DISCUSSION"}

# Check game state after timer expires
curl http://localhost:8000/api/games/{game_id}
# Expected: {"state": "DAY_VOTING"}
```

**Frontend:**
- See "Day Phase - Discussion" with timer "5:00"
- Chat with other players
- Timer counts down to "0:00"
- Auto-transition to Voting Phase

---

## Step 12: Voting Phase

### Backend Tasks
1. **Write Tests First** (`tests/test_voting.py`)
   ```python
   def test_player_can_vote():
       game_id = ...
       voter_id = ...
       target_id = ...

       response = client.post(
           f"/api/games/{game_id}/players/{voter_id}/vote",
           json={"target_player_id": target_id},
           headers={"X-Player-ID": voter_id}
       )
       assert response.status_code == 200

   def test_player_cannot_vote_twice():
       game_id = ...
       voter_id = ...

       # Vote once
       client.post(
           f"/api/games/{game_id}/players/{voter_id}/vote",
           json={"target_player_id": "..."},
           headers={"X-Player-ID": voter_id}
       )

       # Try to vote again
       response = client.post(
           f"/api/games/{game_id}/players/{voter_id}/vote",
           json={"target_player_id": "..."},
           headers={"X-Player-ID": voter_id}
       )
       assert response.status_code == 400

   def test_get_vote_status():
       game_id = ...

       response = client.get(f"/api/games/{game_id}/votes")
       assert response.status_code == 200
       assert "votes" in response.json()
       assert "votes_cast" in response.json()
       assert "total_players" in response.json()

   def test_auto_transition_after_all_votes():
       game_id = ...

       # All players vote
       for player_id in all_player_ids:
           client.post(
               f"/api/games/{game_id}/players/{player_id}/vote",
               json={"target_player_id": "..."},
               headers={"X-Player-ID": player_id}
           )

       # Game should auto-transition to RESULTS
       response = client.get(f"/api/games/{game_id}")
       assert response.json()["state"] == "RESULTS"
   ```

2. **Implement voting logic**
   - Record votes in Vote table
   - Track vote count
   - Auto-transition to RESULTS when all players voted

3. **Implement endpoints**
   - `POST /api/games/{game_id}/players/{player_id}/vote` - Cast vote
   - `GET /api/games/{game_id}/votes` - Get vote status

### Frontend Tasks
1. **Create Voting Phase UI**
   - Show "Day Phase - Voting" header
   - Display all players around board
   - Clickable player avatars (vote by clicking)
   - Confirmation dialog: "Vote to kill [player]?"
   - Show vote status: "3/5 players have voted"
   - No chat during voting (disabled)

2. **Real-time vote updates**
   - Poll vote status
   - Show checkmarks on players who voted
   - Auto-transition when all votes cast

### Demo
**Backend:**
```bash
# Cast vote
curl -X POST http://localhost:8000/api/games/{game_id}/players/{voter_id}/vote \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: {voter_id}" \
  -d '{"target_player_id": "{target_id}"}'
# Expected: {"status": "vote_recorded"}

# Get vote status
curl http://localhost:8000/api/games/{game_id}/votes
# Expected: {
#   "votes": [{"voter_id": "...", "target_id": "..."}],
#   "votes_cast": 3,
#   "total_players": 5
# }

# After all votes, check game state
curl http://localhost:8000/api/games/{game_id}
# Expected: {"state": "RESULTS"}
```

**Frontend:**
- See "Voting Phase"
- Click on Bob's avatar
- Confirm: "Vote to kill Bob?"
- See "You voted for Bob"
- See vote count: "3/5 players have voted"
- When 5/5, auto-transition to Results

---

## Step 13: Results & Win Conditions

### Backend Tasks
1. **Write Tests First** (`tests/test_results.py`)
   ```python
   def test_calculate_deaths():
       game_id = ...

       # Assume votes: Alice(3), Bob(1), Charlie(1)
       # Alice should die (most votes)

       response = client.get(f"/api/games/{game_id}/results")
       assert response.status_code == 200
       assert alice_id in response.json()["deaths"]

   def test_village_wins_if_werewolf_dies():
       # Setup: Alice is Werewolf, gets most votes
       game_id = ...

       response = client.get(f"/api/games/{game_id}/results")
       results = response.json()

       assert results["winning_team"] == "village"

       # All village team members should be winners
       for player in results["players"]:
           if player["team"] == "village":
               assert player["won"] == True

   def test_werewolf_wins_if_no_werewolf_dies():
       # Setup: All werewolves are in center or survived
       game_id = ...

       response = client.get(f"/api/games/{game_id}/results")
       results = response.json()

       assert results["winning_team"] == "werewolf"

   def test_tanner_wins_if_tanner_dies():
       # Setup: Tanner gets killed
       game_id = ...
       tanner_id = ...

       response = client.get(f"/api/games/{game_id}/results")
       results = response.json()

       # Only Tanner wins
       tanner_player = next(p for p in results["players"] if p["player_id"] == tanner_id)
       assert tanner_player["won"] == True

       # Everyone else loses
       for player in results["players"]:
           if player["player_id"] != tanner_id:
               assert player["won"] == False

   def test_hunter_kills_pointed_player():
       # Setup: Hunter dies and points at target
       game_id = ...
       hunter_id = ...
       target_id = ...

       # (Hunter voting implemented as pointing - whoever they voted for)

       response = client.get(f"/api/games/{game_id}/results")
       results = response.json()

       # Both Hunter and target should be dead
       assert hunter_id in results["deaths"]
       assert target_id in results["deaths"]
   ```

2. **Implement win condition logic**
   - Count votes, determine who dies (ties = all tied players die)
   - Apply Hunter effect (if Hunter dies, kill their vote target too)
   - Determine final roles for all players (after night swaps)
   - Determine teams (village, werewolf, tanner)
   - Calculate winners based on rules:
     - Village wins: at least one werewolf dies
     - Werewolf wins: no werewolves die
     - Tanner wins: only if Tanner dies (everyone else loses)
     - Minion special cases
   - Record results

3. **Implement endpoints**
   - `GET /api/games/{game_id}/results` - Get full results

### Frontend Tasks
1. **Create Results Phase UI**
   - Show "Results" header
   - Display vote counts for each player
   - Show who died
   - Reveal all final roles (show role cards face-up)
   - Show team assignments (color-coded: green=village, red=werewolf, purple=tanner)
   - Show winners announcement: "VILLAGE WINS!" or "WEREWOLVES WIN!" or "TANNER WINS!"
   - List individual player results (name, final role, team, win/loss)
   - "Play Another Game" and "End Game Set" buttons

### Demo
**Backend:**
```bash
# Get results
curl http://localhost:8000/api/games/{game_id}/results
# Expected: {
#   "deaths": ["alice_id"],
#   "winning_team": "village",
#   "players": [
#     {
#       "player_id": "alice_id",
#       "player_name": "Alice",
#       "initial_role": "Werewolf",
#       "final_role": "Werewolf",
#       "team": "werewolf",
#       "died": true,
#       "won": false
#     },
#     {
#       "player_id": "bob_id",
#       "player_name": "Bob",
#       "initial_role": "Seer",
#       "final_role": "Seer",
#       "team": "village",
#       "died": false,
#       "won": true
#     },
#     ...
#   ],
#   "vote_summary": {
#     "alice_id": 3,
#     "bob_id": 1,
#     "charlie_id": 1
#   }
# }
```

**Frontend:**
- See "Results" screen
- Vote counts: "Alice: 3 votes ☠️, Bob: 1 vote, Charlie: 1 vote"
- "Alice has died!"
- Show all players with face-up role cards
- "Alice was: WEREWOLF (died)"
- "Bob was: SEER (survived)"
- Big banner: "🎉 VILLAGE WINS! 🎉"
- Green highlighting for village team members (winners)
- Buttons: "Play Another Game" | "End Game Set"

---

## Step 14: Multi-Game Support & Scoring

### Backend Tasks
1. **Write Tests First** (`tests/test_multi_game.py`)
   ```python
   def test_create_second_game_in_set():
       game_set_id = ...
       first_game_id = ...

       # First game is in RESULTS state

       # Start new game
       response = client.post(f"/api/game-sets/{game_set_id}/games")
       assert response.status_code == 201

       new_game = response.json()
       assert new_game["game_id"] != first_game_id
       assert new_game["game_number"] == 2
       assert new_game["state"] == "NIGHT"

   def test_roles_reshuffled_for_new_game():
       game_set_id = ...

       # Play first game, note roles
       first_game_id = ...
       alice_role_game1 = get_player_role(first_game_id, alice_id)

       # Start second game
       response = client.post(f"/api/game-sets/{game_set_id}/games")
       second_game_id = response.json()["game_id"]

       # Roles should be different (likely, not guaranteed)
       alice_role_game2 = get_player_role(second_game_id, alice_id)
       # Just check that new roles were assigned
       assert alice_role_game2["initial_role"] is not None

   def test_get_cumulative_scores():
       game_set_id = ...

       # After playing 2 games
       response = client.get(f"/api/game-sets/{game_set_id}/scores")
       assert response.status_code == 200

       scores = response.json()["scores"]
       assert len(scores) > 0

       # Each player should have wins/losses count
       alice_score = next(s for s in scores if s["player_id"] == alice_id)
       assert "wins" in alice_score
       assert "losses" in alice_score
       assert alice_score["wins"] + alice_score["losses"] == 2  # 2 games played
   ```

2. **Implement multi-game logic**
   - Create new game in same game set
   - Increment game_number
   - Re-shuffle and assign roles
   - Return to NIGHT state

3. **Implement score calculation**
   - Query all games in game set
   - For each game, determine winners
   - Aggregate wins/losses per player

4. **Implement endpoints**
   - `POST /api/game-sets/{game_set_id}/games` - Create new game in set
   - `GET /api/game-sets/{game_set_id}/scores` - Get cumulative scores

### Frontend Tasks
1. **Update Results Page**
   - Show "Game 2 of [current set]" at top
   - Add cumulative score table:
     - Player name
     - Total wins
     - Total losses

2. **Implement "Play Another Game" button**
   - Call `POST /api/game-sets/{game_set_id}/games`
   - Transition back to role reveal (NIGHT state)

3. **Implement "End Game Set" button**
   - Return to lobby/landing page

### Demo
**Backend:**
```bash
# After first game completes, start second game
curl -X POST http://localhost:8000/api/game-sets/{game_set_id}/games
# Expected: {"game_id": "new_game_id", "game_number": 2, "state": "NIGHT"}

# Get cumulative scores
curl http://localhost:8000/api/game-sets/{game_set_id}/scores
# Expected: {
#   "scores": [
#     {"player_id": "alice_id", "player_name": "Alice", "wins": 1, "losses": 1},
#     {"player_id": "bob_id", "player_name": "Bob", "wins": 2, "losses": 0},
#     ...
#   ]
# }
```

**Frontend:**
- On Results page, see:
  - "Game 2 Results"
  - Current game results
  - Cumulative Scores table:
    - Alice: 1 win, 1 loss
    - Bob: 2 wins, 0 losses
- Click "Play Another Game"
- Start new game (back to role reveal for Game 3)

---

## Step 15: WebSocket Real-time Updates

### Backend Tasks
1. **Write Tests First** (`tests/test_websocket.py`)
   ```python
   def test_websocket_connection():
       with client.websocket_connect(f"/ws/games/{game_id}") as websocket:
           # Connection should succeed
           data = websocket.receive_json()
           assert data["type"] == "connection_established"

   def test_game_state_updates_broadcast():
       with client.websocket_connect(f"/ws/games/{game_id}") as ws:
           # Perform action (e.g., vote)
           client.post(f"/api/games/{game_id}/players/{player_id}/vote", ...)

           # Should receive update via websocket
           data = ws.receive_json()
           assert data["type"] == "game_state_update"
           assert data["state"] == "RESULTS"  # Or whatever new state

   def test_chat_messages_broadcast():
       with client.websocket_connect(f"/ws/games/{game_id}") as ws:
           # Send chat message
           client.post(f"/api/games/{game_id}/chat", json={"message": "Hello"})

           # Should receive via websocket
           data = ws.receive_json()
           assert data["type"] == "chat_message"
           assert data["message"] == "Hello"
   ```

2. **Implement WebSocket support**
   - WebSocket endpoint: `/ws/games/{game_id}`
   - Connection manager for each game
   - Broadcast game state changes to all connected players
   - Broadcast chat messages
   - Broadcast night phase updates
   - Broadcast vote updates

3. **Update existing endpoints to broadcast**
   - After any state change, broadcast to all connected clients

### Frontend Tasks
1. **Implement WebSocket client**
   - Connect when entering game page
   - Listen for game state updates
   - Update Zustand store when receiving updates
   - Reconnect on disconnect

2. **Remove polling**
   - Replace polling with WebSocket listeners
   - Much more efficient and real-time

### Demo
**Backend:**
```bash
# Test with websocat or similar tool
websocat ws://localhost:8000/ws/games/{game_id}
# Should see: {"type": "connection_established"}

# In another terminal, perform action
curl -X POST http://localhost:8000/api/games/{game_id}/players/{player_id}/vote ...

# In websocat terminal, should see:
# {"type": "game_state_update", "state": "RESULTS"}
```

**Frontend:**
- Open game in two browser windows (two different players)
- Player 1 votes
- Player 2 immediately sees vote count update (no delay)
- No more 2-second polling lag

---

## Step 16: Chat System

### Backend Tasks
1. **Write Tests First** (`tests/test_chat.py`)
   ```python
   def test_send_chat_message():
       game_set_id = ...
       player_id = ...

       response = client.post(
           f"/api/game-sets/{game_set_id}/chat",
           json={"message": "Hello everyone!"},
           headers={"X-Player-ID": player_id}
       )
       assert response.status_code == 201

   def test_get_chat_history():
       game_set_id = ...

       response = client.get(f"/api/game-sets/{game_set_id}/chat")
       assert response.status_code == 200
       assert len(response.json()["messages"]) > 0

   def test_chat_persists_across_games():
       game_set_id = ...

       # Send message in game 1
       client.post(f"/api/game-sets/{game_set_id}/chat", ...)

       # Start game 2
       client.post(f"/api/game-sets/{game_set_id}/games")

       # Chat history should still include game 1 message
       response = client.get(f"/api/game-sets/{game_set_id}/chat")
       assert len(response.json()["messages"]) > 0
   ```

2. **Implement chat endpoints**
   - `POST /api/game-sets/{game_set_id}/chat` - Send message
   - `GET /api/game-sets/{game_set_id}/chat` - Get history
   - Broadcast chat messages via WebSocket

### Frontend Tasks
1. **Create Chat Component** (persistent across all phases)
   - Chat box in sidebar or bottom panel
   - Message list (scrollable)
   - Input field and send button
   - Show player name with each message
   - Auto-scroll to newest message

2. **Integrate with WebSocket**
   - Send messages via API
   - Receive new messages via WebSocket
   - Update UI in real-time

### Demo
**Backend:**
```bash
# Send chat message
curl -X POST http://localhost:8000/api/game-sets/{game_set_id}/chat \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: {player_id}" \
  -d '{"message": "I think Alice is the werewolf!"}'
# Expected: {"message_id": "...", "status": "sent"}

# Get chat history
curl http://localhost:8000/api/game-sets/{game_set_id}/chat
# Expected: {
#   "messages": [
#     {
#       "message_id": "...",
#       "player_id": "bob_id",
#       "player_name": "Bob",
#       "message": "I think Alice is the werewolf!",
#       "timestamp": "2026-02-01T12:34:56Z"
#     }
#   ]
# }
```

**Frontend:**
- See chat box on right side of screen
- Type: "I think Alice is the werewolf!"
- Press Enter or click Send
- Message appears immediately in both browser windows
- Chat persists across all game phases

---

## Step 17: Additional Roles (Minion, Mason, Tanner, Hunter)

### Backend Tasks
1. **Write Tests First** (`tests/test_additional_roles.py`)
   ```python
   def test_minion_sees_werewolves():
       # Setup: Game with Minion and Werewolves
       game_id = ...
       minion_id = ...

       response = client.get(
           f"/api/games/{game_id}/players/{minion_id}/night-info",
           headers={"X-Player-ID": minion_id}
       )
       assert response.json()["role"] == "Minion"
       assert len(response.json()["werewolves"]) >= 1

   def test_masons_see_each_other():
       # Setup: Game with 2 Masons
       game_id = ...
       mason1_id = ...

       response = client.get(
           f"/api/games/{game_id}/players/{mason1_id}/night-info",
           headers={"X-Player-ID": mason1_id}
       )
       assert response.json()["role"] == "Mason"
       assert "other_mason" in response.json()

   def test_minion_wins_with_werewolves():
       # Setup: Minion + Werewolves, no werewolves die
       game_id = ...

       results = client.get(f"/api/games/{game_id}/results").json()

       minion_player = next(p for p in results["players"] if p["final_role"] == "Minion")
       assert minion_player["won"] == True

   def test_tanner_only_wins_if_dies():
       # Setup: Tanner dies
       game_id = ...

       results = client.get(f"/api/games/{game_id}/results").json()

       # Only Tanner wins, everyone else loses
       for player in results["players"]:
           if player["final_role"] == "Tanner":
               assert player["won"] == True
           else:
               assert player["won"] == False

   def test_hunter_kills_vote_target():
       # Setup: Hunter dies, voted for Bob
       # (Hunter's vote indicates who they're pointing at)
       game_id = ...

       results = client.get(f"/api/games/{game_id}/results").json()

       # Both Hunter and Bob should be dead
       hunter_player = next(p for p in results["players"] if p["final_role"] == "Hunter")
       bob_player = next(p for p in results["players"] if p["player_name"] == "Bob")

       assert hunter_player["died"] == True
       assert bob_player["died"] == True
   ```

2. **Implement additional roles**
   - Minion: Auto-show werewolves (similar to werewolf info display)
   - Mason: Auto-show other mason
   - Tanner: Special win condition (only wins if dies, everyone else loses)
   - Hunter: Kill vote target if Hunter dies
   - Update win condition logic

3. **Update night phase orchestration**
   - Add roles to wake order (Minion after Werewolf, Mason after Minion)

### Frontend Tasks
1. **Create role-specific UI**
   - Minion turn: "You are the Minion. The werewolves are: [names]"
   - Mason turn: "You are a Mason. The other Mason is: [name]"
   - Tanner: No night action (just reveal)
   - Hunter: No night action (just reveal)

2. **Update Results UI**
   - Show Tanner win condition: "TANNER WINS! Everyone else loses."
   - Show Hunter effect: "Hunter died and killed [target]!"

### Demo
**Backend:**
```bash
# Minion views werewolves
curl http://localhost:8000/api/games/{game_id}/players/{minion_id}/night-info \
  -H "X-Player-ID: {minion_id}"
# Expected: {"role": "Minion", "werewolves": [{"player_id": "...", "player_name": "Alice"}]}

# Results with Tanner win
curl http://localhost:8000/api/games/{game_id}/results
# Expected: {"winning_team": "tanner", ...}
```

**Frontend:**
- Minion sees: "You are the Minion. The werewolves are: Alice, Bob"
- Mason sees: "You are a Mason. The other Mason is: Charlie"
- Results: "TANNER WINS!" (if Tanner died)

---

## Step 18: Polish & Error Handling

### Backend Tasks
1. **Write Tests First** (`tests/test_error_handling.py`)
   ```python
   def test_404_for_invalid_game_id():
       response = client.get("/api/games/invalid-id")
       assert response.status_code == 404

   def test_400_for_invalid_role_action():
       # Non-Seer tries to perform Seer action
       response = client.post(
           f"/api/games/{game_id}/players/{werewolf_id}/seer-action",
           ...
       )
       assert response.status_code == 400 or response.status_code == 403

   def test_cannot_join_full_game_set():
       # Game set with 5 players, 5 already joined
       response = client.post(f"/api/game-sets/{game_set_id}/players/{player6_id}/join")
       assert response.status_code == 400
   ```

2. **Add error handling**
   - Proper HTTP status codes
   - Clear error messages
   - Validation for all inputs
   - Handle edge cases (e.g., all werewolves in center)

3. **Add logging**
   - Log all game actions
   - Log errors for debugging

### Frontend Tasks
1. **Add error handling**
   - Show toast notifications for errors
   - Handle network failures gracefully
   - Retry failed WebSocket connections

2. **Add loading states**
   - Loading spinners during API calls
   - Skeleton screens for game board

3. **Polish UI**
   - Add smooth transitions
   - Improve card flip animations
   - Better visual feedback for actions

### Demo
**Backend:**
```bash
# Try invalid action
curl -X POST http://localhost:8000/api/games/{game_id}/players/{werewolf_id}/seer-action \
  -H "X-Player-ID: {werewolf_id}" \
  ...
# Expected: 400 {"error": "Player is not the Seer"}

# Try to join full game
curl -X POST http://localhost:8000/api/game-sets/{game_set_id}/players/{player6_id}/join
# Expected: 400 {"error": "Game set is full"}
```

**Frontend:**
- Network fails: See "Connection lost. Retrying..." toast
- Action fails: See "Invalid action" error toast
- Loading: See spinner while waiting for API response

---

## Step 19: Testing & Documentation

### Tasks
1. **Run full test suite**
   ```bash
   # Backend
   pytest tests/ -v --cov

   # Aim for >80% coverage on core logic
   ```

2. **Write API documentation**
   - OpenAPI/Swagger docs (auto-generated by FastAPI)
   - Add docstrings to all endpoints
   - Document WebSocket protocol

3. **Write README**
   - Setup instructions
   - How to run locally
   - Game rules reference
   - Architecture overview

### Demo
```bash
# Run tests
pytest tests/ -v
# All tests should pass

# View API docs
# Visit http://localhost:8000/docs
# See interactive Swagger UI with all endpoints
```

---

## Step 20: Deployment Prep

### Tasks
1. **Environment configuration**
   - Separate dev/prod configs
   - Environment variables for secrets
   - Database URL configuration

2. **Docker setup** (optional)
   - Dockerfile for backend
   - Dockerfile for frontend
   - docker-compose for local development

3. **Production optimizations**
   - Frontend: Next.js production build
   - Backend: Gunicorn/Uvicorn workers
   - Database: Consider PostgreSQL for production (SQLite OK for small deployments)

### Demo
```bash
# Build production frontend
cd frontend
npm run build
npm run start

# Run production backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Or with Docker
docker-compose up
```

---

## Summary

This implementation plan provides:
- **20 clear steps** with incremental progress
- **Demonstrable results** at each step (both frontend UI and backend curl examples)
- **TDD approach** with tests written first
- **Focus on main functionality** (not every edge case)
- **Balanced work** between frontend and backend
- **Clear stopping points** where you can pause and review progress

Each step builds on the previous one, allowing you to track progress and see the game come together piece by piece.
