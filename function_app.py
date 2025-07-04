import logging
import azure.functions as func
from datetime import datetime, timezone, timedelta
from azure_updates import azure_updates

app = func.FunctionApp()

@app.timer_trigger(schedule="3 0 0 * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def timer_trigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    # 日付が変わった直後 UTC 0:00:03 にタイマーで起動され、その前日に更新された情報を取得する。
    date_time = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%dT00:00:00Z')
    logging.info(f'Fetch Azure Updates - modified ge {date_time}.')
    azure_updates(date_time)
    logging.info('Azure Updates JPN timer trigger function executed.')