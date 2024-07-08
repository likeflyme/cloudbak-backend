from db.sys_db import SessionLocal
from app.models.sys import SysUser, SysSession
from app.dependencies.auth_dep import pwd_context

session = SessionLocal()

try:
    password = pwd_context.hash('secret')
    user = SysUser(username='admin', password=password,nickname='nickname', state=1)
    session.add(user)
    session.commit()

    sys_session = SysSession(name='mmxc', wx_id='wxid_x1j6ne5cnl8r19', wx_acct_name='MMXC', owner_id=user.id)
    session.add(sys_session)
    session.commit()
finally:
    session.close()
