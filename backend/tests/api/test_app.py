async def test_operation_ids_are_unique_route_names(api_client) -> None:
    response = await api_client.get("/api/openapi.json")

    operation_ids = [
        operation["operationId"] for path in response.json()["paths"].values() for operation in path.values()
    ]
    assert len(operation_ids) == len(set(operation_ids))
    assert "list_clubs" in operation_ids
