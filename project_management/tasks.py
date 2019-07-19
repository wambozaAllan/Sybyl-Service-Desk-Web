from background_task import background
from .models import User


@background(schedule=60)
def notify_user(user_id):
    # lookup user by id and send them a message
    print('xxxxxxxxxx``````````````````````````xxxxxxxxxxxxxxxxxxxxxxxxxx `````````````')
    user = User.objects.get(pk=user_id)
    print('-----------------------------------------------------------------------TASKS RUNNING--------')
    print(user)
    