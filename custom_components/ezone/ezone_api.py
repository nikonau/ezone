import xml.etree.ElementTree as ET
import asyncio
import aiohttp

ON = "1"
OFF = "0"


class ApiError(Exception):
    """EZone API Error"""


class ezone_api:
    """EZone Connection"""

    def __init__(self, ip: str, port: int = 2025, session: aiohttp.ClientSession = None, retry: int = 5):
        if session is None:
            session = aiohttp.ClientSession()

        self.ip = ip
        self.port = port
        self.session = session
        self.retry = retry

    async def async_get_system_data(self, retry: int = None):
        """Get system data from EZone controller"""
        retry = retry or self.retry
        count = 0
        error = None
        
        while count < retry:
            count += 1
            try:
                async with self.session.get(
                    f"http://{self.ip}:{self.port}/getSystemData",
                    timeout=aiohttp.ClientTimeout(total=4),
                ) as resp:
                    assert resp.status == 200
                    xml_data = await resp.text()
                    return self._parse_system_xml(xml_data)
            except (
                aiohttp.ClientError,
                aiohttp.ClientConnectorError,
                aiohttp.client_exceptions.ServerDisconnectedError,
                ConnectionResetError,
            ) as err:
                error = err
            except asyncio.TimeoutError:
                error = "Connection timed out."
            except AssertionError:
                error = "Response status not 200."
                break
            except Exception as err:
                error = f"XML parsing error: {err}"
                break

            await asyncio.sleep(1)
        
        raise ApiError(
            f"No valid response after {count} failed attempt{['','s'][count>1]}. Last error was: {error}"
        )

    async def async_get_zone_data(self, zone: int, retry: int = None):
        """Get zone data from EZone controller"""
        retry = retry or self.retry
        count = 0
        error = None
        
        while count < retry:
            count += 1
            try:
                async with self.session.get(
                    f"http://{self.ip}:{self.port}/getZoneData",
                    params={"zone": zone},
                    timeout=aiohttp.ClientTimeout(total=4),
                ) as resp:
                    assert resp.status == 200
                    xml_data = await resp.text()
                    return self._parse_zone_xml(xml_data, zone)
            except (
                aiohttp.ClientError,
                aiohttp.ClientConnectorError,
                aiohttp.client_exceptions.ServerDisconnectedError,
                ConnectionResetError,
            ) as err:
                error = err
            except asyncio.TimeoutError:
                error = "Connection timed out."
            except AssertionError:
                error = "Response status not 200."
                break
            except Exception as err:
                error = f"XML parsing error: {err}"
                break

            await asyncio.sleep(1)
        
        raise ApiError(
            f"No valid response after {count} failed attempt{['','s'][count>1]}. Last error was: {error}"
        )

    async def async_get_all_data(self):
        """Get all system and zone data"""
        try:
            # Get system data
            system_data = await self.async_get_system_data()
            
            # Get zone data for each zone
            num_zones = int(system_data.get("system", {}).get("unitcontrol", {}).get("numberOfZones", 0))
            zones_data = {}
            
            for zone_num in range(1, num_zones + 1):
                try:
                    zone_data = await self.async_get_zone_data(zone_num)
                    zones_data[str(zone_num)] = zone_data
                except ApiError:
                    # Continue if a zone fails
                    continue
            
            # Combine system and zone data
            result = {
                "system": system_data.get("system", {}),
                "zones": zones_data
            }
            
            return result
            
        except Exception as err:
            raise ApiError(f"Failed to get all data: {err}")

    def _parse_system_xml(self, xml_data: str) -> dict:
        """Parse system XML response"""
        try:
            root = ET.fromstring(xml_data)
            return self._xml_to_dict(root)
        except ET.ParseError as err:
            raise ApiError(f"Invalid XML response: {err}")

    def _parse_zone_xml(self, xml_data: str, zone_num: int) -> dict:
        """Parse zone XML response"""
        try:
            root = ET.fromstring(xml_data)
            zone_data = self._xml_to_dict(root)
            zone_data["zone_number"] = zone_num
            return zone_data
        except ET.ParseError as err:
            raise ApiError(f"Invalid XML response: {err}")

    def _xml_to_dict(self, element) -> dict:
        """Convert XML element to dictionary"""
        result = {}
        
        # Add element text if it exists and has no children
        if element.text and element.text.strip() and len(element) == 0:
            return element.text.strip()
        
        # Process child elements
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                # Handle multiple elements with same tag
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result

    async def async_set_system_data(self, **params):
        """Set system data on EZone controller"""
        try:
            async with self.session.get(
                f"http://{self.ip}:{self.port}/setSystemData",
                params=params,
                timeout=aiohttp.ClientTimeout(total=4),
            ) as resp:
                assert resp.status == 200
                return await resp.text()
        except Exception as err:
            raise ApiError(f"Failed to set system data: {err}")

    async def async_set_zone_data(self, zone: int, **params):
        """Set zone data on EZone controller"""
        try:
            zone_params = {"zone": zone, **params}
            async with self.session.get(
                f"http://{self.ip}:{self.port}/setZoneData",
                params=zone_params,
                timeout=aiohttp.ClientTimeout(total=4),
            ) as resp:
                assert resp.status == 200
                return await resp.text()
        except Exception as err:
            raise ApiError(f"Failed to set zone data: {err}")

    # Convenience methods for common operations
    async def async_set_aircon_on_off(self, state: bool):
        """Turn aircon on/off"""
        return await self.async_set_system_data(airconOnOff=1 if state else 0)

    async def async_set_mode(self, mode: int):
        """Set aircon mode (1=cool, 2=heat, 3=fan)"""
        return await self.async_set_system_data(mode=mode)

    async def async_set_fan_speed(self, speed: int):
        """Set fan speed (1=low, 2=medium, 3=high)"""
        return await self.async_set_system_data(fanSpeed=speed)

    async def async_set_target_temp(self, temp: float):
        """Set target temperature"""
        return await self.async_set_system_data(centralDesiredTemp=temp)

    async def async_set_zone_setting(self, zone: int, setting: bool):
        """Turn zone on/off"""
        return await self.async_set_zone_data(zone, zoneSetting=1 if setting else 0)

    async def async_set_zone_percent(self, zone: int, percent: int):
        """Set zone damper percentage (0-100)"""
        return await self.async_set_zone_data(zone, userPercentSetting=percent, zoneSetting=1)

    async def async_set_zone_name(self, zone: int, name: str):
        """Set zone name"""
        return await self.async_set_zone_data(zone, name=name)

    async def async_change_system_name(self, name: str):
        """Change system name"""
        try:
            async with self.session.get(
                f"http://{self.ip}:{self.port}/changeName",
                params={"name": name},
                timeout=aiohttp.ClientTimeout(total=4),
            ) as resp:
                assert resp.status == 200
                return await resp.text()
        except Exception as err:
            raise ApiError(f"Failed to change system name: {err}")

    async def async_get_zone_timer(self):
        """Get zone timer information"""
        try:
            async with self.session.get(
                f"http://{self.ip}:{self.port}/getZoneTimer",
                timeout=aiohttp.ClientTimeout(total=4),
            ) as resp:
                assert resp.status == 200
                xml_data = await resp.text()
                return self._parse_system_xml(xml_data)
        except Exception as err:
            raise ApiError(f"Failed to get zone timer: {err}")

    async def async_set_zone_timer(self, start_hour: int = None, start_min: int = None, 
                                  end_hour: int = None, end_min: int = None, 
                                  schedule_status: int = 0):
        """Set zone timer schedule
        
        Args:
            start_hour: Start time hour (0-23)
            start_min: Start time minutes (0-59)
            end_hour: End time hour (0-23)
            end_min: End time minutes (0-59)
            schedule_status: 0=off, 1=on, 2=?, 3=?
        """
        params = {"scheduleStatus": schedule_status}
        
        if start_hour is not None:
            params["startTimeHours"] = start_hour
        if start_min is not None:
            params["startTimeMinutes"] = start_min
        if end_hour is not None:
            params["endTimeHours"] = end_hour
        if end_min is not None:
            params["endTimeMinutes"] = end_min
            
        try:
            async with self.session.get(
                f"http://{self.ip}:{self.port}/setZoneTimer",
                params=params,
                timeout=aiohttp.ClientTimeout(total=4),
            ) as resp:
                assert resp.status == 200
                return await resp.text()
        except Exception as err:
            raise ApiError(f"Failed to set zone timer: {err}")
