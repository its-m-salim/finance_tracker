from connection import*



async def create_user(full_name, username, tg_id):
    try:
        conn = await connection_db()
        await conn.execute("""
        insert into users(full_name, username, telegram_id) values
            ($1, $2, $3)
""", full_name, username, str(tg_id))
    except Exception as error:
        print(f"{type(error)}: {error} ser.py")     
    finally:
        await conn.close()   


async def profile(tg_id):
    try:
        conn = await connection_db()
        user = await conn.fetchrow("""
        select * from users
        where telegram_id = $1
""", str(tg_id))
        return user
    except Exception as error:
        print(f"{type(error)}: {error} ser.py")     
    finally:
        await conn.close()   


async def make_transactions(caption, tg_id, amount, transaction_type):
    try:
        conn = await connection_db()
        if transaction_type == "withdraw":
            result = await conn.execute("""
                update users
                SET balance = balance - $1
                where telegram_id = $2 AND balance >= $1
            """, amount, str(tg_id))
            if result == "update 0":
                return False

        else:
            result = await conn.execute("""
                update users
                SET balance = balance + $1
                where telegram_id = $2
            """, amount, str(tg_id))
            if result == "update 0":
                return False

        await conn.execute("""
            insert into  transiction_h
                (caption, type, telegram_id, amount)
            values ($1, $2, $3, $4)
        """, caption, transaction_type, str(tg_id), amount)
        return True

    except Exception as error:
        print(f"{type(error)}: {error} s.py")
        return False
    finally:
        if conn is not None:
            await conn.close()


async def get_transictions(tg_id):
    try:
        conn = await connection_db()
        transictions = await conn.fetch("""
        select * from transiction_h
        where telegram_id = $1
        order by created_at desc, id desc
""", str(tg_id))
        return transictions
    except Exception as error:
        print(f"{type(error)}: {error} s.py")     
    finally:
        await conn.close()   

async def get_tr_type(tg_id, type):
    try:
        conn = await connection_db()
        transictions = await conn.fetch("""
        select * from transiction_h
        where telegram_id = $1 and type = $2
        order by created_at desc, id desc
    """, str(tg_id), type)
        return transictions
    except Exception as error:
        print(f"{type(error)}: {error} s.py")     
    finally:
        await conn.close()   


async def get_last_tr(tg_id):
    try:
        conn = await connection_db()
        transiction = await conn.fetch("""
        select * from transiction_h
        where telegram_id = $1 
        order by created_at desc, id desc
        limit 1
    """, str(tg_id))
        return transiction
    except Exception as error:
        print(f"{type(error)}: {error} s.py")     
    finally:
        await conn.close()   
        
async def get_biggest_tr(tg_id):
    try:
        conn = await connection_db()
        transiction = await conn.fetch("""
        select * from transiction_h
        where telegram_id = $1 
        order by amount desc, created_at desc
        limit 1
    """, str(tg_id))
        return transiction
    except Exception as error:
        print(f"{type(error)}: {error} s.py")     
    finally:
        await conn.close()  



async def create_goal_credit(caption, amount, tg_id, type):
    try:
        conn = await connection_db()
        await conn.execute("""
        insert into goals(type, caption, amount, telegram_id) values
            ($1, $2, $3, $4)
""", type, caption, amount, str(tg_id))
        return True
    except Exception as error:
        print(f"{type(error)}: {error} s.py")     
    finally:
        await conn.close()   



#либо принимает tuple с длиной 1 для получения всех типов , либо 2
async def get_goals(tg_id, types, types2):
    try:
        conn = await connection_db()
        goals = await conn.fetch("""
        select * from goals
        where telegram_id = $1 and (type = $2 or type = $3) 
        order by created_at desc, id desc
""", str(tg_id), types, types2)
        return goals
    except Exception as error:
        print(f"{type(error)}: {error} sg.py")     
    finally:
        await conn.close()





def check_amount(text):
    try:
        amount = int(text)
    except ValueError:
        return "Сумма должна быть целым числом, например: 10"
    if amount < 0:
        return "Сумма не может быть отрицательной"
    if amount == 0:
        return "Сумма не может быть равна нулю"
    return None


async def pay_goal_credit(amount, g_id, tg_id, goal_type):
    try:
        conn = await connection_db()   
        result = await conn.execute("""
        UPDATE goals
        SET current_amount = LEAST(current_amount + $1, amount),
            status = LEAST(current_amount + $1, amount) >= amount
        WHERE id = $2
        and telegram_id = $3
        and type = $4
""", amount, int(g_id), str(tg_id), goal_type)
        if result == "update 0":
            return False
        elif result == "update 1":
            if goal_type == "credit":
                await conn.execute("""
                insert into  transiction_h
                    (caption, type, telegram_id, amount)
                values ($1, $2, $3, $4)
                """, f"withdraw for credit", goal_type, str(tg_id), amount)
            return True
    except Exception as error:
        print(f"{type(error)}: {error} s.py")
        return False     
    finally:
        await conn.close()


async def get_status(tg_id, goal_id):
    try:
        conn = await connection_db()
        status = await conn.fetchrow("""
        select * from goals
        where id = $1 and telegram_id = $2
""", int(goal_id), str(tg_id))
        if status:
            await conn.execute("""
        update goals 
        set is_active = False
        where id = $1 and telegram_id = $2
""", int(goal_id), str(tg_id))
        status = await conn.fetchrow("""
                select * from goals
                where id = $1 and telegram_id = $2
        """, int(goal_id), str(tg_id))
        return status
    except Exception as error:
        print(f"{type(error)}: {error} s.py")     
    finally:
        await conn.close()   