from app.models.sys import SysSession
from db.sys_db import SessionLocal
from app.services.analyze import analyze
from app.services.sys_task_maker import task_execute, TaskObj

# print('# analyze 执行第一次 ============================================================')
# analyze(8)
# print('# analyze 执行第二次 ============================================================')
# analyze(8)

for i in range(1, 5):
    print(f'# task_execute 执行第 {i} 次 ============================================================')
    task_obj = TaskObj(1, f"数据解析-内存测试", analyze, 8)
    task_execute(task_obj)





