import "./styles.css";
import data from "@city-data";
import { CITIES } from "./config";
import { start } from "./app";
import type { CityData } from "./types";

start(data as unknown as CityData, CITIES[__CITY__]);
