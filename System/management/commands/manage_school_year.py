from django.core.management.base import BaseCommand
from System.models import SchoolYear
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Manages school year transitions and creates new school years automatically'

    def handle(self, *args, **options):
        try:
            # Get current date for logging
            current_date = datetime.now()
            self.stdout.write(f"Running school year management check on {current_date.strftime('%Y-%m-%d')}")

            # Try to get current school year
            current_school_year = SchoolYear.get_current_school_year()
            self.stdout.write(f"Current active school year: {current_school_year.year}")

            # Check for transition
            new_school_year = SchoolYear.transition_to_new_school_year()
            
            if new_school_year != current_school_year:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully transitioned to new school year: {new_school_year.year}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"No transition needed. Current school year {current_school_year.year} is still active."
                    )
                )

        except Exception as e:
            logger.error(f"Error in school year management: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f"Error occurred: {str(e)}")
            ) 