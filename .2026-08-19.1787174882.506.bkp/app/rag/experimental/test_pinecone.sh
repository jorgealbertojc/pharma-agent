#!/bin/bash

curl -X POST \
  "http://localhost:5081/vectors/upsert" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": [
      {
        "id": "test-vector-1",
        "values": [
          0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
          0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1
        ]
      }
    ]
  }'
