CREATE TABLE cards (
       card_id INT NOT NULL PRIMARY KEY,
       card_name text NOT NULL,
       card_type text NOT NULL,
       card_subtype text NOT NULL,
       card_attribute text,
       monster_type text,
       monster_class text,
       monster_level INT,
       monster_atk INT,
       monster_def INT,
       card_text text NOT NULL);
