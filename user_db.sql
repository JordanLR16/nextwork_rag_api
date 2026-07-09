CREATE TABLE IF NOT EXISTS people (
	id INT PRIMARY KEY,
	first_name VARCHAR(255),
	last_name VARCHAR(255),
	age INT,
	skill_level VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS recipes (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author_name VARCHAR(255) NOT NULL,
    ingredients TEXT NOT NULL DEFAULT '[]',
    instructions TEXT NOT NULL,
    substitutions TEXT NOT NULL DEFAULT '[]',
    tagline VARCHAR(255),
    description TEXT,
    tags TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS ix_recipes_id ON recipes (id);