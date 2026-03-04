#### Enter API
http://127.0.0.1:8000/api/entry/
POST Request
multipart/form-data
```
	`license_plate` -> String
	`entry_image` ->File (Image)
	`camera_id` ->Integer
```

	
Response
```
{
    `"status": "success",`
    `"message": "Vehicle entry recorded",`
    `"log_id": 45,`
    `"entry_time": "2024-05-20T14:30:00Z"`
}
```
___
#### Exit API
http://127.0.0.1:8000/api/exit/
POST Request
multipart/form-data
```
	`license_plate`: (String)
	`exit_image`: (File)
```

Response
```
{
    `"status": "success",`
    `"entry_time": "2024-05-20T10:00:00Z",`
    `"exit_time": "2024-05-20T14:30:00Z",`
    `"duration_hours": 4.5,`
    `"total_fee": 45.00`
}
```
___

#### Slots Update API (Bulk)

[http://127.0.0.1:8000/api/slots/update/](https://www.google.com/search?q=http://127.0.0.1:8000/api/slots/update/) 
POST Request 
**application/json**
```
[
    {
        "slot_id": "A1",
        "is_occupied": true
    },
    {
        "slot_id": "A2",
        "is_occupied": false
    }
]
```

**Response**
```
{
    "status": "success",
    "updated_slots": ["A1", "A2"],
    "message": "Successfully updated 2 slots"
}
```

---


#### Parking Summary API

[http://127.0.0.1:8000/api/status/summary/]
GET Request
**Response**

```
{
    "total_slots": 100,
    "available": 65,
    "occupied": 25,
    "reserved": 10
}
```