from django.core.management.base import BaseCommand
from apps.ai_engine.seed_vector_store import main as seed_main
from apps.ai_engine.vector_store import vector_store

class Command(BaseCommand):
    help = 'Seed the ChromaDB vector store with travel data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all collections before seeding (WARNING: Deletes existing data)',
        )
        
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show vector store statistics only',
        )

    def handle(self, *args, **options):
        if options['stats']:
            self.stdout.write(self.style.SUCCESS('\nVector Store Statistics:'))
            stats = vector_store.get_collection_stats()
            self.stdout.write(f"  Destinations: {stats.get('destinations', 0)}")
            self.stdout.write(f"  Activities: {stats.get('activities', 0)}")
            self.stdout.write(f"  Local Experiences: {stats.get('experiences', 0)}")
            self.stdout.write(f"  Travel Tips: {stats.get('tips', 0)}")
            self.stdout.write(f"  Total Documents: {stats.get('total', 0)}\n")
            return
        
        if options['reset']:
            self.stdout.write(self.style.WARNING('\n⚠️  Resetting all collections...'))
            confirm = input('Are you sure? This will delete all data (yes/no): ')
            if confirm.lower() == 'yes':
                vector_store.reset_collections()
                self.stdout.write(self.style.SUCCESS('✓ Collections reset\n'))
            else:
                self.stdout.write(self.style.ERROR('Cancelled\n'))
                return
        
        self.stdout.write(self.style.SUCCESS('Starting vector store seeding...\n'))
        seed_main()
        self.stdout.write(self.style.SUCCESS('\n✨ Seeding complete!'))