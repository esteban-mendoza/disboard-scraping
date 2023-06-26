-- Drop servers table
DROP TABLE IF EXISTS public.disboard_servers;

-- Create servers table
CREATE TABLE public.disboard_servers (
    scrape_time FLOAT,
    platform_link VARCHAR(25),
    guild_id VARCHAR(19),
    discord_invite_code VARCHAR(255),
    server_name VARCHAR(255),
    server_description TEXT,
    tags JSONB,
    category VARCHAR(255)
);
