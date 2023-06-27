-- Drop servers table
DROP TABLE IF EXISTS public.disboard_servers;

-- Create servers table
CREATE TABLE public.disboard_servers (
    scrape_time FLOAT,
    platform_link VARCHAR(40),
    guild_id VARCHAR(40),
    server_name VARCHAR(255),
    server_description TEXT,
    tags JSONB,
    category VARCHAR(255),
    PRIMARY KEY (guild_id)
);

-- Create guild_id index
CREATE INDEX disboard_servers_guild_id_index ON public.disboard_servers (guild_id);
