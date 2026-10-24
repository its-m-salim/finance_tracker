from dotenv import load_dotenv
import asyncpg
import os

load_dotenv()

p_db = os.getenv("PASSWORD_DB")


async def connection_db():
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="salim",
            database="tracker",
            password=p_db
        )
        return conn
    except Exception as error:
        print(f"{type(error)}: {error} conn.py")



async def create_tables():
    try:
        conn = await connection_db()
        await conn.execute("""
        create table if not exists users(
            id serial primary key,
            full_name varchar(200) not null,
            username varchar(200),
            telegram_id varchar(200) unique not null,
            balance int not null default 0 check (balance >= 0),
            created_at timestamp default now(),
            is_active bool default true
        );

        create table if not exists transiction_h(
            id serial primary key,
            caption text not null,
            type varchar(20) not null check (type in ('withdraw', 'deposit')),
            telegram_id varchar(200) not null references users(telegram_id),
            amount int not null check (amount > 0),
            status bool not null default true,
            created_at timestamp default now(),
            is_active bool default true
        );

        create table if not exists goals(
            id serial primary key,
            type varchar(20) not null check (type in ('goal', 'credit')),
            caption text not null ,
            telegram_id varchar(200) not null references users(telegram_id),
            amount int not null check (amount > 0),
            current_amount int not null default 0,
            created_at timestamp default now(),
            status bool not null default false,
            is_active bool default true,
            check (current_amount >= 0 and current_amount <= amount),
            check (status = (current_amount >= amount))
                );

""")
        print("Таблицы базы данных успешно проверены/созданы.")
    except Exception as error:
        print(f"{type(error)}: {error} con.py")     
    finally:
        await conn.close()   

        