"""webif Object.

A webif object that contains a webif item and communicates with the webif.
It contains a webif client for setting and getting webif values
"""

import logging

import aiohttp
from bs4 import BeautifulSoup
from bs4.element import NavigableString, ResultSet, Tag

from .configentry import MyConfigEntry
from .const import CONF

logging.basicConfig()
log: logging.Logger = logging.getLogger(name=__name__)


class WebifConnection:
    """Connect to the local Weishaupt Webif."""

    _config_entry: MyConfigEntry = None
    _ip: str = ""
    _username: str = ""
    _password: str = ""
    _session = None
    _payload: dict[str, str] = {"user": _username, "pass": _password}
    _base_url: str = "http://" + _ip
    _login_url: str = "/login.html"
    _connected: bool = False
    _values = {}

    def __init__(self, config_entry: MyConfigEntry) -> None:
        """Initialize the WebIf connection.

        Todo: Get info from config.

        """
        self._ip = config_entry.data[CONF.HOST]
        self._username = config_entry.data[CONF.USERNAME]
        self._password = config_entry.data[CONF.PASSWORD]
        self._base_url = "http://" + self._ip
        self._config_entry = config_entry

    async def login(self) -> None:
        """Log into the portal. Create cookie to stay logged in for the session."""
        jar = aiohttp.CookieJar(unsafe=True)
        self._session = aiohttp.ClientSession(base_url=self._base_url, cookie_jar=jar)
        if self._username != "" and self._password != "":
            async with self._session.post(
                "login.html",
                data={"user": self._username, "pass": self._password},
            ) as response:
                if response.status == 200:
                    self._connected = True
                else:
                    self._connected = False
        else:
            logging.log("No user / password specified for webif")
            self._connected = False

    async def return_test_data(self) -> dict[str, str]:
        """Return some values for testing."""

        return {
            "Webifsensor": "TESTWERT",
            "Außentemperatur": 2,
            "AT Mittelwert": -1,
            "AT Langzeitwert": -1,
            "Raumsolltemperatur": 22.0,
            "Vorlaufsolltemperatur": 32.5,
            "Vorlauftemperatur": 32.4,
        }

    async def close(self) -> None:
        """Close connection to WebIf."""
        await self._session.close()

    async def get_info(self) -> None:
        """Return Info -> Heizkreis1."""
        if self._connected == False:
            return None
        async with self._session.get(
            url="/settings_export.html?stack=0C00000100000000008000F9AF010002000301,0C000C1900000000000000F9AF020003000401"
        ) as response:
            if response.status != 200:
                logging.debug(msg="Error: " & str(response.status))
                return None
            # logging.debug(msg=await response.text())
            # print(await response.text())
            main_page = BeautifulSoup(
                markup=await response.text(), features="html.parser"
            )
            navs: Tag | NavigableString | None = main_page.findAll(
                "div", class_="col-3"
            )
            # print(navs)

            if len(navs) == 3:
                values_nav = navs[2]
                self._values["Info"] = {"Heizkreis": self.get_values(soup=values_nav)}
                logging.debug(msg=self._values)
                return self._values["Info"]["Heizkreis"]
            else:
                logging.debug("Update failed. return None")
                print(await response.text())
                print(navs)
                return None

    def get_links(self, soup: BeautifulSoup) -> dict:
        """Return links from given nav container."""
        soup_links = soup.find_all(name="a")
        links = {}
        for link in soup_links:
            # print(link)
            # print(link.name)
            name = link.find("h5").text.strip()
            url = link["href"]
            links[name] = url
            # print(name + ": " + url)
            # link = link.find("a")
            # print(name + ":" + link)
        return links

    def get_values(self, soup: BeautifulSoup) -> dict:
        """Return values from given nav container."""
        soup_links = soup.find_all(name="div", class_="nav-link browseobj")
        # print(soup_links)
        values = {}
        for item in soup_links:
            # print(link)
            # print(item.name)
            name = item.find("h5").text.strip()
            value = item.findAll(string=True, recursive=False)
            myValue = value[1].strip()
            if len(myValue.split(" ")) > 1:
                myNumber = myValue.split(" ")[0]
                values[name] = myNumber
            else:
                values[name] = myValue
            # print(name + ": " + url)
            # link = link.find("a")
            # print(name + ":" + link)
        return values

    def get_link_values(self, soup: BeautifulSoup) -> dict:
        """Return values from given nav container witch are inside a link."""
        soup_links: ResultSet[logging.Any] = soup.find_all(
            name="a", class_="nav-link browseobj"
        )
        # print(soup_links)
        values = {}
        for item in soup_links:
            # print(link)
            # print(item.name)
            name = item.find("h5").text.strip()
            value = item.findAll(string=True, recursive=False)
            values[name] = value[1].strip()
            # print(name + ": " + url)
            # link = link.find("a")
            # print(name + ":" + link)
        return values
