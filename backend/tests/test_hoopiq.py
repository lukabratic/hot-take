"""Unit tests for the HoopIQ endpoint."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient, ASGITransport

from main import app
from models import Player, Roll, RollPlayer
from schemas import RollHoopIQResponse, PlayerHoopIQResponse


def _make_player(player_id: int, position: str) -> MagicMock:
    """Create a mock Player with stats."""
    player = MagicMock(spec=Player)
    player.id = player_id
    player.name = f"Player {player_id}"
    player.position = position
    player.career_stats = {"pts": 20.0, "reb": 5.0, "ast": 4.0, "stl": 1.0, "blk": 0.5, "per": 22.0, "bpm": 3.0, "vorp": 4.0, "ws": 100.0}
    player.peak_stats = {"pts": 28.0, "reb": 7.0, "ast": 6.0, "stl": 1.5, "blk": 1.0, "per": 28.0, "bpm": 7.0, "vorp": 8.0, "ws": 15.0}
    player.playoff_stats = {"pts": 22.0, "reb": 6.0, "ast": 5.0, "stl": 1.2, "blk": 0.8, "per": 24.0, "bpm": 5.0, "vorp": 3.0, "ws": 10.0}
    return player


class TestHoopIQEndpoint:
    """Tests for GET /api/hoopiq endpoint."""

    @pytest.mark.asyncio
    async def test_returns_roll_with_players(self):
        """HoopIQ endpoint returns a roll with anonymized player data."""
        mock_players = [_make_player(i, "PG") for i in range(1, 8)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_players

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        # session.add is synchronous in SQLAlchemy
        added_objects = []
        mock_session.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

        # Mock the Roll ID assignment during flush
        async def mock_flush():
            for obj in added_objects:
                if isinstance(obj, Roll):
                    obj.id = 42

        mock_session.flush.side_effect = mock_flush

        async def mock_get_session():
            yield mock_session

        app.dependency_overrides = {}
        from database import get_session
        app.dependency_overrides[get_session] = mock_get_session

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                with patch("rolls.router.generate_roll", return_value={"position": "PG", "theme_modifier": "All-Time"}):
                    response = await client.get("/api/hoopiq")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 42
            assert data["position"] == "PG"
            assert data["theme_modifier"] == "All-Time"
            assert data["mode"] == "hoopiq"
            assert 5 <= len(data["players"]) <= 7

            # Verify players have stats but no names
            for player in data["players"]:
                assert "id" in player
                assert "career_stats" in player
                assert "peak_stats" in player
                # HoopIQ should NOT include name, position, era, team info
                assert "name" not in player
                assert "position" not in player
                assert "era" not in player
                assert "bbref_id" not in player
        finally:
            app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_returns_correct_stats_structure(self):
        """HoopIQ players have properly structured stats."""
        mock_players = [_make_player(i, "SG") for i in range(1, 8)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_players

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        added_objects = []
        mock_session.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

        async def mock_flush():
            for obj in added_objects:
                if isinstance(obj, Roll):
                    obj.id = 99

        mock_session.flush.side_effect = mock_flush

        async def mock_get_session():
            yield mock_session

        from database import get_session
        app.dependency_overrides[get_session] = mock_get_session

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                with patch("rolls.router.generate_roll", return_value={"position": "SG", "theme_modifier": "Peak Season Only"}):
                    response = await client.get("/api/hoopiq")

            assert response.status_code == 200
            data = response.json()

            # Check stats fields are present
            player = data["players"][0]
            career = player["career_stats"]
            assert "pts" in career
            assert "reb" in career
            assert "ast" in career
            assert "per" in career
            assert "bpm" in career
            assert "vorp" in career
            assert "ws" in career

            peak = player["peak_stats"]
            assert "pts" in peak
        finally:
            app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_insufficient_players_returns_500(self):
        """HoopIQ endpoint returns 500 when not enough players exist."""
        # Only 2 players available, but need 5-7
        mock_players = [_make_player(i, "C") for i in range(1, 3)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_players

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        async def mock_get_session():
            yield mock_session

        from database import get_session
        app.dependency_overrides[get_session] = mock_get_session

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                with patch("rolls.router.generate_roll", return_value={"position": "C", "theme_modifier": "All-Time"}):
                    response = await client.get("/api/hoopiq")

            assert response.status_code == 500
            assert "Insufficient players" in response.json()["detail"]
        finally:
            app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_no_auth_required(self):
        """HoopIQ endpoint works without authentication."""
        mock_players = [_make_player(i, "SF") for i in range(1, 8)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_players

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        added_objects = []
        mock_session.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

        async def mock_flush():
            for obj in added_objects:
                if isinstance(obj, Roll):
                    obj.id = 10

        mock_session.flush.side_effect = mock_flush

        async def mock_get_session():
            yield mock_session

        from database import get_session
        app.dependency_overrides[get_session] = mock_get_session

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                with patch("rolls.router.generate_roll", return_value={"position": "SF", "theme_modifier": "Playoff Performance"}):
                    # No Authorization header
                    response = await client.get("/api/hoopiq")

            assert response.status_code == 200
        finally:
            app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_persists_roll_and_roll_players(self):
        """HoopIQ endpoint creates Roll and RollPlayer records in database."""
        mock_players = [_make_player(i, "PF") for i in range(1, 8)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_players

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        added_objects = []

        # session.add is synchronous in SQLAlchemy, use MagicMock not AsyncMock
        mock_session.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

        async def mock_flush():
            for obj in added_objects:
                if isinstance(obj, Roll):
                    obj.id = 55

        mock_session.flush.side_effect = mock_flush

        async def mock_get_session():
            yield mock_session

        from database import get_session
        app.dependency_overrides[get_session] = mock_get_session

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                with patch("rolls.router.generate_roll", return_value={"position": "PF", "theme_modifier": "Defensive Impact"}):
                    with patch("rolls.router.random.randint", return_value=5):
                        response = await client.get("/api/hoopiq")

            assert response.status_code == 200

            # Verify Roll was created
            rolls_created = [obj for obj in added_objects if isinstance(obj, Roll)]
            assert len(rolls_created) == 1
            assert rolls_created[0].mode == "hoopiq"
            assert rolls_created[0].position == "PF"
            assert rolls_created[0].theme_modifier == "Defensive Impact"

            # Verify RollPlayers were created (should be 5 since we patched randint)
            roll_players_created = [obj for obj in added_objects if isinstance(obj, RollPlayer)]
            assert len(roll_players_created) == 5

            # Verify commit was called
            mock_session.commit.assert_called_once()
        finally:
            app.dependency_overrides = {}
