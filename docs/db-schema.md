erDiagram
    USER ||--o{ RESERVATION : makes
    PLAY ||--o{ PERFORMANCE : has
    THEATRE_HALL ||--o{ PERFORMANCE : hosts
    PERFORMANCE ||--o{ TICKET : has
    RESERVATION ||--o{ TICKET : includes
    PLAY }o--o{ ACTOR : casts
    PLAY }o--o{ GENRE : categorized

    USER {
        bigint id PK
        -- Django auth user (AUTH_USER_MODEL)
    }

    ACTOR {
        bigint id PK
        varchar first_name (<=50)
        varchar last_name  (<=50)
        image  avatar (default: actors/default.png)
    }

    GENRE {
        bigint id PK
        varchar name (<=50, unique)
    }

    PLAY {
        bigint id PK
        varchar title (<=50, unique)
        text    description (<=255)
        image   image (default: plays/default.png)
        -- M2M: actors, genres
    }

    THEATRE_HALL {
        bigint id PK
        varchar name (<=20, unique)
        int     rows (>=1)
        int     seats_in_row (>=1)
    }

    PERFORMANCE {
        bigint id PK
        bigint play_id FK -> PLAY.id (CASCADE)
        bigint theatre_hall_id FK -> THEATRE_HALL.id (CASCADE)
        datetime show_time (indexed)
    }

    RESERVATION {
        bigint id PK
        datetime created_at (auto_now_add)
        bigint user_id FK -> USER.id (CASCADE)
        -- index (user, created_at)
    }

    TICKET {
        bigint id PK
        int    row (>=1)
        int    seat (>=1)
        bigint performance_id FK -> PERFORMANCE.id (CASCADE)
        bigint reservation_id FK -> RESERVATION.id (CASCADE)
        -- unique (performance, row, seat)
    }
