import logging
from datetime import datetime
from typing import List

import aiohttp
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from schemas import Temperature
from .. import crud, schemas
from dependencies import get_db

router = APIRouter()

API_KEY = "844066ec80254d2bada71850240207"


@router.post("/update", response_model=List[Temperature])
async def update_temperatures(
    db: Session = Depends(get_db),
) -> List[Temperature]:
    cities = crud.get_all_cities(db)
    temperatures = []
    async with aiohttp.ClientSession() as session:
        for city in cities:
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': city.name,
                'appid': API_KEY
            }
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logging.error(
                        f"Failed to fetch weather data for city: {city.name},"
                        f" status: {response.status}"
                    )
                    continue
                data = await response.json()
                logging.info(f"Received data for city {city.name}: {data}")

                if "main" not in data:
                    logging.error(
                        f"No 'main' key in response data for city: {city.name}"
                    )
                    continue

                temperature = data["main"]["temp"] - 273.15
                temp_record = schemas.TemperatureCreate(
                    city_id=city.id,
                    date_time=datetime.now(),
                    temperature=temperature,
                )
                temperatures.append(temp_record)
                crud.create_temperature(db=db, temperature=temp_record)

    return temperatures


@router.get("/", response_model=List[Temperature])
def read_temperatures(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> List[Temperature]:
    temperatures = crud.get_all_temperatures(db, skip=skip, limit=limit)
    return temperatures


@router.get("/by_city", response_model=List[Temperature])
def read_temperatures_by_city(
    city_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[Temperature]:
    temperatures = crud.get_temperatures_by_city(
        db, city_id=city_id, skip=skip, limit=limit
    )
    return temperatures
