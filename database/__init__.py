import sqlite3, logging
from typing import Optional


class DatabaseManager:
    def __init__(self):
        self.connection = sqlite3.connect("database/rankings.db")
        self.cursor = self.connection.cursor()

    async def get_match_history(self, discord_id: Optional[int] = None, player_name: Optional[str] = None):
        if discord_id:
            try:
                # Selects player and joins (or uses index?) with matches
                pass
            except sqlite3.OperationalError:
                logging.log(logging.ERROR, "Useful error message")
        elif player_name:
            try:
                # Selects player and joins (or uses index?) with matches
                pass
            except sqlite3.OperationalError:
                logging.log(logging.ERROR, "Useful error message")
        return None

    async def set_player(self, discord_id: int, name: str):
        """
        Adds a player to the database

        :param discord_id: players discord id
        :param name: players name (lowercase)
        :return: Success (boolean)
        """
        try:
            self.cursor.execute("INSERT INTO players (discord_id, username) VALUES (? ?)", (discord_id, name))
            self.connection.commit()
            return True
        except sqlite3.OperationalError as e:
            logging.log(logging.ERROR, f"OperationalError during set_player {e}")
            return False
