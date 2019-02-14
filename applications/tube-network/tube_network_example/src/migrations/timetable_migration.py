# Copyright 2018 Grakn Labs Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import grakn
import json
import os
import tube_network_example.settings as settings
import multiprocessing
import datetime as dt

def entity_template(data):
    query = "insert $x isa " + data["type"]
    for attribute in data["attributes"]:
        query += ", has " + attribute["type"] + " " + str(attribute["value"])
    query += ";"
    return query


def relationship_template(data):
    query = "match "
    for i, roleplayer in enumerate(data["roleplayers"]):
        query += "$" + str(i) + " has " + roleplayer["key_type"] + " " + str(roleplayer["key_value"]) + "; "

    # match the relationship if required
    if "key_type" in data:
        query += "$x has " + data["key_type"] + " " + str(data["key_value"]) + "; "


    query += "insert $x ("
    for i, roleplayer in enumerate(data["roleplayers"]):
        query += roleplayer["role_name"] + ": $" + str(i)
        if i < len(data["roleplayers"]) - 1:
            query += ", "

    if "key_type" in data:
        query += ")"
    else:
        query += ") isa " + data["type"]

    if "attributes" in data:
        query += "; $x"
        for attribute in data["attributes"]:
            query += " has " + attribute["type"] + " " + attribute["value"]
    query += ";"
    return query


def string(value): return '"' + value + '"'


def unique_append(list, key, item):
    if item not in list[key]:
        list[key].append(item)

def zone_already_added(zone_name):
    zone_already_added = False
    for zone_query in relationship_queries["zone"]:
        if 'isa zone; $x has name "' + zone_name + '"' in zone_query:
            zone_already_added = True
            break
    return zone_already_added


def construct_queries(entity_queries, relationship_queries):
    timetable_files = os.listdir(settings.timetables_path)

    for timetable_file in timetable_files:
        with open(settings.timetables_path + "/" + timetable_file) as template_file:
            data = json.load(template_file)

            unique_append(entity_queries, "tube-line",
                entity_template(
                    {
                        "type": "tube-line",
                        "attributes": [
                            {
                                "type": "name",
                                "value": string(data["lineName"])
                            }
                        ]
                    }
                )
            )

            for i, station in enumerate(data["stops"]):
                unique_append(entity_queries, "station",
                    entity_template(
                        {
                            "type": "station",
                            "attributes": [
                                {
                                    "type": "naptan-id",
                                    "value": string(station["id"])
                                },
                                {
                                    "type": "lon",
                                    "value": station["lon"]
                                },
                                {
                                    "type": "lat",
                                    "value": station["lat"]
                                },
                                {
                                    "type": "name",
                                    "value": string(station["name"])
                                }
                            ]
                        }
                    )
                )

                if "zone" in station:
                    if zone_already_added(station["zone"]):
                        unique_append(relationship_queries, "zone",
                            relationship_template(
                                {
                                    "type": "zone",
                                    "key_type": "name",
                                    "key_value": string(station["zone"]),
                                    "roleplayers": [
                                        {
                                            "type": "station",
                                            "key_type": "naptan-id",
                                            "key_value": string(station["id"]),
                                            "role_name": "contained-station"
                                        }
                                    ]
                                }
                            )
                        )
                    else:
                        unique_append(relationship_queries, "zone",
                            relationship_template(
                                {
                                    "type": "zone",
                                    "roleplayers": [
                                        {
                                            "type": "station",
                                            "key_type": "naptan-id",
                                            "key_value": string(station["id"]),
                                            "role_name": "contained-station"
                                        }
                                    ],
                                    "attributes": [
                                        {
                                            "type": "name",
                                            "value": string(station["zone"])
                                        }
                                    ]
                                }
                            )
                        )

                for r, route in enumerate(data['timetable']["routes"]):
                    route_identifier = timetable_file.split(".")[0] + str(r)
                    unique_append(relationship_queries, "route",
                        relationship_template(
                            {
                                "type": "route",
                                "roleplayers": [
                                    {
                                        "type": "tube-line",
                                        "key_type": "name",
                                        "key_value": string(data["lineName"]),
                                        "role_name": "route-operator"
                                    }
                                ],
                                "attributes": [
                                    {
                                        "type": "identifier",
                                        "value": string(route_identifier)
                                    }
                                ]
                            }
                        )
                    )

                    intervals = route["stationIntervals"][0]["intervals"] # first set of intervals is sufficient
                    for i, interval in enumerate(intervals): # first station is the origin
                        if i == 0:
                            unique_append(relationship_queries, "route",
                                relationship_template(
                                    {
                                        "type": "route",
                                        "key_type": "identifier",
                                        "key_value": string(route_identifier),
                                        "roleplayers": [
                                            {
                                                "type": "station",
                                                "key_type": "naptan-id",
                                                "key_value": string(interval["stopId"]),
                                                "role_name": "origin"
                                            }
                                        ]
                                    }
                                )
                            )
                        elif i == len(intervals) - 1: # last station is the destination
                            unique_append(relationship_queries, "route",
                                relationship_template(
                                    {
                                        "type": "route",
                                        "key_type": "identifier",
                                        "key_value": string(route_identifier),
                                        "roleplayers": [
                                            {
                                                "type": "station",
                                                "key_type": "naptan-id",
                                                "key_value": string(interval["stopId"]),
                                                "role_name": "destination"
                                            }
                                        ]
                                    }
                                )
                            )
                        else: # any other station is an ordinary stop
                            unique_append(relationship_queries, "route",
                                relationship_template(
                                    {
                                        "type": "route",
                                        "key_type": "identifier",
                                        "key_value": string(route_identifier),
                                        "roleplayers": [
                                            {
                                                "type": "station",
                                                "key_type": "naptan-id",
                                                "key_value": string(interval["stopId"]),
                                                "role_name": "stop"
                                            }
                                        ]
                                    }
                                )
                            )

                        if i < len(intervals) - 1: # there is no more stop after the last one
                            last_time_to_arrival = 0
                            duration = int(interval["timeToArrival"] - last_time_to_arrival)
                            route_section_identifier = timetable_file.split(".")[0] + "_route_section_" + str(i)
                            unique_append(entity_queries, "route-section",
                                entity_template(
                                    {
                                        "type": "route-section",
                                        "attributes": [
                                            {
                                                "type": "duration",
                                                "value": duration
                                            },
                                            {
                                                "type": "identifier",
                                                "value": string(route_section_identifier)
                                            }
                                        ]
                                    }
                                )
                            )
                            last_time_to_arrival = interval["timeToArrival"]

                            tunnel_identifier = timetable_file.split(".")[0] + "_tunnel_" + str(i)
                            unique_append(relationship_queries, "tunnel",
                                relationship_template(
                                    {
                                        "type": "tunnel",
                                        "roleplayers": [
                                            {
                                                "type": "station",
                                                "key_type": "naptan-id",
                                                "key_value": string(interval["stopId"]), # current stop
                                                "role_name": "beginning"
                                            },
                                            {
                                                "type": "station",
                                                "key_type": "naptan-id",
                                                "key_value": string(intervals[i+1]["stopId"]), # next stop
                                                "role_name": "end"
                                            },
                                            {
                                                "type": "route-section",
                                                "key_type": "identifier",
                                                "key_value": string(route_section_identifier),
                                                "role_name": "service"
                                            }
                                        ],
                                        "attributes": [
                                            {
                                                "type": "identifier",
                                                "value": string(tunnel_identifier)
                                            }
                                        ]
                                    }
                                )
                            )

def insert(queries):
    client = grakn.Grakn(uri=settings.uri)
    with client.session(keyspace=settings.keyspace) as session:
        transaction = session.transaction(grakn.TxType.WRITE)
        for i, query in enumerate(queries):
            print(query)
            print("- - - - - - - - - - - - - -")
            transaction.query(query)

            if i % 500 == 0:
                transaction.commit()
                transaction = session.transaction(grakn.TxType.WRITE)
        transaction.commit()


def insert_concurrently(queries, processes):
    cpu_count = multiprocessing.cpu_count()
    chunk_size = int(len(queries)/cpu_count)

    for i in range(cpu_count):
        if i == cpu_count - 1:
            chunk = queries[i*chunk_size:]
        else:
            chunk = queries[i*chunk_size:(i+1)*chunk_size]

        process = multiprocessing.Process(target=insert, args=(chunk,))
        process.start()
        processes.append(process)

    for process in processes:
        process.join()


if __name__ == "__main__":
    start_time = dt.datetime.now()

    entity_queries = { "tube-line": [], "station": [], "route-section": [] }
    relationship_queries = { "zone": [], "route": [], "tunnel": [] }

    construct_queries(entity_queries, relationship_queries)

    entities, relationships = [], []
    for k, v in entity_queries.items(): entities += v
    for k, v in relationship_queries.items(): relationships += v

    entity_processes = []
    relationship_processes = []

    insert_concurrently(entities, entity_processes)
    insert_concurrently(relationships, relationship_processes)

    end_time = dt.datetime.now()
    print("- - - - - -\nTime taken: " + str(end_time - start_time))
    print("\n" + str(len(entity_processes)) + " processes used to insert Entities.")
    print("\n" + str(len(relationship_processes)) + " processes used to insert Relationship.")