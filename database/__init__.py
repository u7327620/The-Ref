import sqlite3, discord, logging
from typing import Optional

INITIAL_ELO = 1500

class DatabaseManager:
    def __init__(self, *, connection: sqlite3.Connection):
        self.connection = connection
        self.cursor = connection.cursor()

    async def lookup_player(self, discord_id: int) -> Optional[int, str, int]:
        """
        Retrieves name and elo of a given discord_id or None if not found

        :param discord_id: id of the player to look up
        :return: row of player information or None
        """
        try:
            self.cursor.execute("SELECT * FROM players WHERE discord_id like ?", (discord_id,))
            return self.cursor.fetchone()
        except sqlite3.OperationalError:
            logging.log(logging.ERROR, "OperationalError during lookup_player")
            return None

    async def add_player(self, discord_id: int, name: str) -> bool:
        """
        Creates a new player in the database

        :param discord_id: discord id of new player
        :param name: toribash name of new player
        :return: Boolean success/failure
        """
        try:
            self.cursor.execute("INSERT INTO players (discord_id, name, elo) VALUES (?, ?, ?)",
                                (discord_id, name.lower(), INITIAL_ELO))
            self.connection.commit()
            return True
        except sqlite3.OperationalError:
            logging.log(logging.ERROR, "OperationalError during add_player")
            return False

    async def remove_player(self, discord_id: int) -> bool:
        """
        Removes a player from rankings database without updating any matches

        :param discord_id: discord id of player to remove
        :return: Boolean success/failure
        """
        try:
            self.cursor.execute("DELETE FROM players WHERE discord_id like ?", (discord_id,))
            self.connection.commit()
            return True
        except sqlite3.OperationalError:
            logging.log(logging.ERROR, "OperationalError during remove_player")
            return False

    async def add_match(self, player1_id: int, player2_id: int) -> bool:
        """
        Adds a match to the database to later be scored.

        :param player1_id: discord id of one player
        :param player2_id: discord id of the other player
        :return: Boolean success/failure
        """
        try:
            self.cursor.execute("INSERT INTO matches (player1_id, player2_id) VALUES (?, ?)",
                                (player1_id, player2_id))
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            logging.log(logging.ERROR, "IntegrityError during add_match")
            return False

    async def remove_match(self, match_id: int) -> bool:
        """
        Removes a match from the database

        :param match_id: id of match to remove
        :return: Boolean success/failure
        """
        try:
            self.cursor.execute("DELETE FROM matches WHERE id like ?", (match_id,))
            self.connection.commit()
            return True
        except sqlite3.OperationalError:
            logging.log(logging.ERROR, "OperationalError during remove_match")
            return False

    async def judge_match(self, match_id: int, p1_points: int, p2_points: int) -> bool:
        """
        Scores a match in the database

        :param match_id: id of match to score
        :param p1_points: p1 points
        :param p2_points:  p2 points
        :return: Boolean success/failure
        """
        try:
            self.cursor.execute("UPDATE matches SET player1_score = ?, player2_score = ? WHERE id like ?",
                                (p1_points, p2_points, match_id))
            self.connection.commit()
            return True
        except sqlite3.OperationalError:
            logging.log(logging.ERROR, "OperationalError during judge_match")
            return False

    async def get_all_players(self) -> list:
        """
        Retrieves all players from the database sorted by elo

        :return: list of all players in descending elo order, or empty list
        """
        try:
            self.cursor.execute("SELECT * FROM players ORDER BY elo DESC")
            return self.cursor.fetchall()
        except sqlite3.OperationalError:
            logging.log(logging.ERROR, "OperationalError during get_all_players")
            return []

    async def get_match_history(self, discord_id: int) -> list:
        """
        Retrieves the match history of a player

        :param discord_id: id of player to retrieve history for
        :return: list of matches the player has played in, or empty list
        """
        try:
            self.cursor.execute("SELECT * FROM matches WHERE player1_id like ? OR player2_id like ?",
                                (discord_id, discord_id))
            return self.cursor.fetchall()
        except sqlite3.OperationalError:
            logging.log(logging.ERROR, "OperationalError during get_match_history")
            return []
