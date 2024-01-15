from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import pytz

#IMPORTING THE SCRAPERS
from news_scraper import venturebeat_scraping
from news_scraper import zdnet_scraping
from news_scraper import techxplore_scraping

cutoff_date = "10-01-2024"
max_pages = 50

#CREATING SCHEDULER INSTANCE
scheduler = BlockingScheduler(timezone=pytz.timezone('Asia/Shanghai'))

#SCHEDULING SCRAPING TASK
scheduler.add_job(venturebeat_scraping, 'cron', day_of_week='mon', hour=10, minute=2, args=[cutoff_date, max_pages], misfire_grace_time=1)
# scheduler.add_job(zdnet_scraping, 'cron', day_of_week='mon', hour=16, minute=53, args=[cutoff_date, max_pages], misfire_grace_time=1)
# scheduler.add_job(techxplore_scraping, 'cron', day_of_week='mon', hour=16, minute=53, args=[cutoff_date, max_pages], misfire_grace_time=1)


try:
    # Start the scheduler
    print("Scheduler started. Press Ctrl+C to exit.")
    scheduler.start()
except KeyboardInterrupt:
    # Stop the scheduler if interrupted
    print("Scheduler stopped.")