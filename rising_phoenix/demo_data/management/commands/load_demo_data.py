"""Loads demo data for the Saaf / Rising Phoenix platform.

Run with:    python manage.py load_demo_data

Wipes the 8 demo users (and everything attached to them via cascade) then
re-creates a full, end-to-end story: 4 requesters, 3 artisans, 1 staff,
workshops, portfolios, completed projects, requests across every status,
proposals across every status, 3 contracts with progress updates/comments/
events, conversations, reviews, notification preferences, one open dispute,
and a couple of reports.

Images live under: <repo>/RisingPhoenix/demo_data/images/<folder>/<file>
"""

import os
import random
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

# Models — one import per app.
from account.models import ArtisanProfile, Profile, Review
from dispute.models import Dispute, DisputeMessage
from invitation.models import Invitation
from message.models import Conversation, Message
from notification.models import Notification, NotificationPreference
from payment.models import PaymentMethod, StripeCustomer
from progress.models import (
    Contract, ContractEvent, ContractEventImage,
    ProgressComment, ProgressCommentImage,
    ProgressImage, ProgressUpdate,
)
from proposal.models import Proposal, ProposalImage
from request.models import Request, RequestImage
from staff.models import Report, StaffProfile
from workshop.models import (
    Category, CompletedProject, CompletedProjectImage,
    PortfolioImage, WorkshopProfile,
)


# ------------------------------------------------------------------------
# Paths and small helpers
# ------------------------------------------------------------------------

# settings.BASE_DIR points to .../RisingPhoenix/rising_phoenix
# Demo images live at .../RisingPhoenix/demo_data/images
DEMO_IMAGES = Path(settings.BASE_DIR).parent / 'demo_data' / 'images'

DEMO_PASSWORD = 'demopass123'


def _attach_image(obj, field_name, image_path):
    """Copy an image file into the ImageField (saves under MEDIA_ROOT/upload_to/)."""
    if not image_path.exists():
        return False
    with open(image_path, 'rb') as f:
        getattr(obj, field_name).save(image_path.name, File(f), save=True)
    return True


def _img(folder, filename):
    """Build a path inside the demo_data/images/<folder>/ tree."""
    return DEMO_IMAGES / folder / filename


# ------------------------------------------------------------------------
# Static demo configuration
# ------------------------------------------------------------------------

DEMO_USERNAMES = [
    'ahmed', 'noura', 'faisal', 'sara',           # requesters
    'laila', 'khalid', 'fahad',                    # artisans
    'staff_admin',                                # staff
]

CATEGORY_DEFS = [
    ('Leather Goods',        'Bags, wallets, belts, accessories.'),
    ('Calligraphy',          'Arabic and Islamic calligraphy art.'),
    ('Woodworking',          'Furniture, shelves, decorative woodwork.'),
    ('Pottery & Ceramics',   'Hand-thrown pottery, mugs, tableware.'),
    ('Metalwork',            'Sculptures, decorative metal, forging.'),
    ('Painting & Art',       'Custom paintings, portraits, abstract.'),
    ('Jewelry',              'Custom rings, pendants, bracelets.'),
    ('Embroidery',           'Thobes, scarves, fabric embroidery.'),
]


# ------------------------------------------------------------------------
# The command
# ------------------------------------------------------------------------

class Command(BaseCommand):
    help = 'Wipes the 8 demo users and re-creates a full demo dataset.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-dispute', action='store_true',
            help='Skip creating the demo dispute thread.',
        )
        parser.add_argument(
            '--no-reports', action='store_true',
            help='Skip creating sample reports.',
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        self.opts = opts
        self.users = {}
        self.profiles = {}
        self.artisan_profiles = {}
        self.workshops = {}
        self.categories = {}
        self.requests = {}
        self.proposals = {}
        self.contracts = {}

        self._cleanup()
        self._create_groups()
        self._create_categories()
        self._create_users_and_profiles()
        self._create_workshops_and_portfolios()
        self._create_completed_projects()
        self._create_requests()
        self._create_proposals()
        self._create_contracts_and_progress()
        self._create_conversations()
        self._create_reviews()
        self._create_invitations()
        self._create_notification_preferences()
        self._create_notifications()
        self._create_payment_methods()
        if not opts['no_dispute']:
            self._create_dispute()
        if not opts['no_reports']:
            self._create_reports()

        self.stdout.write(self.style.SUCCESS('\n  Demo data loaded.'))
        self.stdout.write(
            f'  Login with any of: {", ".join(DEMO_USERNAMES)}  /  password: {DEMO_PASSWORD}\n'
        )

    # --------------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------------
    def _cleanup(self):
        self.stdout.write('  Wiping previous demo users (if any)...')
        deleted, _ = User.objects.filter(username__in=DEMO_USERNAMES).delete()
        self.stdout.write(f'    removed {deleted} rows')

    # --------------------------------------------------------------------
    # Groups
    # --------------------------------------------------------------------
    def _create_groups(self):
        self.artisan_group, _ = Group.objects.get_or_create(name='artisan')

    # --------------------------------------------------------------------
    # Categories
    # --------------------------------------------------------------------
    def _create_categories(self):
        self.stdout.write('  Creating categories...')
        for name, desc in CATEGORY_DEFS:
            cat, _ = Category.objects.get_or_create(name=name, defaults={'description': desc})
            self.categories[name] = cat

    # --------------------------------------------------------------------
    # Users + profiles
    # --------------------------------------------------------------------
    def _create_users_and_profiles(self):
        self.stdout.write('  Creating users + profiles...')

        # Requesters: (username, first, last, phone, bio, avatar_filename)
        requesters = [
            ('ahmed',  'Ahmed',  'Al-Otaibi', '+966512345001',
             'Riyadh-based, into custom decor for my new apartment.',
             'avatar_ahmed.jpg'),
            ('noura',  'Noura',  'Al-Mutairi', '+966512345002',
             'Looking for thoughtful, handmade gifts.',
             'avatar_noura.jpg'),
            ('faisal', 'Faisal', 'Al-Harbi',  '+966512345003',
             'Architect. I appreciate detail and craft.',
             'avatar_faisal.jpg'),
            ('sara',   'Sara',   'Al-Qahtani','+966512345004',
             'Interior designer. Always sourcing one-of-a-kind pieces.',
             'avatar_sara.jpg'),
        ]
        for username, first, last, phone, bio, avatar in requesters:
            u = User.objects.create_user(
                username=username, password=DEMO_PASSWORD,
                first_name=first, last_name=last,
                email=f'{username}@example.com',
            )
            p = Profile.objects.create(user=u, phone=phone, bio=bio, is_phone_verified=True)
            avatar_path = _img('avatars', avatar)
            if avatar_path.exists():
                _attach_image(p, 'avatar', avatar_path)
            self.users[username] = u
            self.profiles[username] = p

        # Artisans
        artisans = [
            ('laila',  'Laila',  'Al-Anazi',  '+966512345005',
             'Leather and calligraphy artisan. 8 years of practice.',
             'avatar_laila.jpg'),
            ('khalid', 'Khalid', 'Al-Dossari','+966512345006',
             'Woodworker and potter. I build what lasts.',
             'avatar_khalid.jpg'),
            ('fahad',   'Fahad',   'Al-Sayed',  '+966512345007',
             'Metalwork, painting, and silver jewelry. Custom work only.',
             'avatar_fahad.jpg'),
        ]
        for username, first, last, phone, bio, avatar in artisans:
            u = User.objects.create_user(
                username=username, password=DEMO_PASSWORD,
                first_name=first, last_name=last,
                email=f'{username}@example.com',
            )
            u.groups.add(self.artisan_group)
            ap = ArtisanProfile.objects.create(
                user=u, phone=phone, bio=bio,
                is_phone_verified=True, is_verified=True,
            )
            avatar_path = _img('avatars', avatar)
            if avatar_path.exists():
                _attach_image(ap, 'avatar', avatar_path)
            self.users[username] = u
            self.artisan_profiles[username] = ap

        # Featured flag — Fahad gets featured
        self.artisan_profiles['fahad'].is_featured = True
        self.artisan_profiles['fahad'].save(update_fields=['is_featured'])

        # Staff
        staff_user = User.objects.create_user(
            username='staff_admin', password=DEMO_PASSWORD,
            first_name='Mohammed', last_name='Admin',
            email='staff@example.com',
            is_staff=True, is_superuser=True,
        )
        sp = StaffProfile.objects.create(
            user=staff_user,
            display_name='Mohammed Admin',
            role='Platform Moderator',
            phone='+966512345008',
            bio='Reviews disputes and reports across the platform.',
        )
        avatar_path = _img('avatars', 'avatar_staff.jpg')
        if avatar_path.exists():
            _attach_image(sp, 'avatar', avatar_path)
        self.users['staff_admin'] = staff_user

    # --------------------------------------------------------------------
    # Workshops, portfolios, completed projects
    # --------------------------------------------------------------------
    def _create_workshops_and_portfolios(self):
        self.stdout.write('  Creating workshops + portfolios...')

        workshop_defs = [
            ('laila', {
                'workshop_name': "Laila's Atelier",
                'tagline':       'Hand-stitched leather and Arabic calligraphy.',
                'description':   ('A small atelier focused on patient, hand-finished work. '
                                  'Leather goods stitched and edge-bevelled by hand; '
                                  'calligraphy in thuluth and diwani scripts on archival paper.'),
                'services':      ('Leather wallets, bags, belts\n'
                                  'Arabic calligraphy framed pieces\n'
                                  'Custom monograms and engraving'),
                'location':      'Riyadh',
                'phone':         '+966512345005',
                'categories':    ['Leather Goods', 'Calligraphy'],
                'portfolio_folder': 'Laila_Atelier',
            }),
            ('khalid', {
                'workshop_name': 'Khalid Craft Studio',
                'tagline':       'Solid wood furniture and hand-thrown ceramics.',
                'description':   ('Furniture and ceramics built one piece at a time. '
                                  'I work with locally-sourced walnut, oak, and stoneware clay.'),
                'services':      ('Custom furniture (tables, shelves, cabinets)\n'
                                  'Ceramic dinnerware sets\n'
                                  'Decorative wooden panels and inlays'),
                'location':      'Jeddah',
                'phone':         '+966512345006',
                'categories':    ['Woodworking', 'Pottery & Ceramics'],
                'portfolio_folder': 'Khalid Craft Studio',
            }),
            ('fahad', {
                'workshop_name': "Fahad's Forge",
                'tagline':       'Metalwork, painting, and silver — bespoke only.',
                'description':   ('Mixed-media studio. Forged copper and iron sculpture, '
                                  'oil and acrylic painting, and one-off silver jewelry.'),
                'services':      ('Metal wall art and sculpture\n'
                                  'Oil and acrylic paintings (portraits + abstract)\n'
                                  'Hand-forged silver rings and pendants'),
                'location':      'Dammam',
                'phone':         '+966512345007',
                'categories':    ['Metalwork', 'Painting & Art', 'Jewelry'],
                'portfolio_folder': 'fahad_forge',
            }),
        ]

        for username, cfg in workshop_defs:
            artisan_profile = self.artisan_profiles[username]
            ws = WorkshopProfile.objects.create(
                artisan=artisan_profile,
                workshop_name=cfg['workshop_name'],
                tagline=cfg['tagline'],
                description=cfg['description'],
                services=cfg['services'],
                location=cfg['location'],
                phone=cfg['phone'],
                is_published=True,
            )
            ws.categories.set([self.categories[c] for c in cfg['categories']])

            # Portfolio images — load every jpg in that artisan's folder.
            portfolio_dir = DEMO_IMAGES / 'workshop_portfolio' / cfg['portfolio_folder']
            portfolio_files = sorted(portfolio_dir.glob('*.jpg')) if portfolio_dir.exists() else []
            for idx, img_path in enumerate(portfolio_files):
                pi = PortfolioImage.objects.create(
                    workshop=ws,
                    is_pinned=(idx < 2),  # pin the first two
                    caption=f'Past work — {cfg["workshop_name"]}',
                )
                _attach_image(pi, 'image', img_path)

            # Workshop cover — reuse the first portfolio image.
            if portfolio_files:
                _attach_image(ws, 'cover_image', portfolio_files[0])

            self.workshops[username] = ws

    def _create_completed_projects(self):
        self.stdout.write('  Creating completed-project showcases...')

        showcase_defs = [
            ('fahad', {
                'title': 'Copper Sunburst Wall Sculpture',
                'description': ('A 1.4 m forged copper sunburst, custom-finished with a '
                                'verdigris patina. Installed in a private villa entry.'),
                'main_image':   _img('completed_projects', 'completed_fahad_main.jpg'),
                'extra_images': [
                    _img('completed_project_images', 'completed_fahad_detail1.jpg'),
                    _img('completed_project_images', 'completed_fahad_install.jpg'),
                ],
                'is_featured': True,
            }),
            ('laila', {
                'title': 'Bespoke Leather Tote with Embossed Monogram',
                'description': ('Vegetable-tanned full-grain leather tote, hand-stitched '
                                'with waxed thread. Monogram blind-embossed on the front panel.'),
                'main_image':   _img('completed_projects', 'completed_laila_main.jpg'),
                'extra_images': [
                    _img('completed_project_images', 'completed_laila_detail1.jpg'),
                    _img('completed_project_images', 'completed_laila_inuse.jpg'),
                ],
                'is_featured': True,
            }),
            ('khalid', {
                'title': 'Walnut Live-Edge Coffee Table',
                'description': ('Single walnut slab on hand-forged hairpin legs. '
                                'Finished with a hard-wax oil to keep the grain matte and natural.'),
                'main_image':   _img('completed_projects', 'completed_khalid_main.jpg'),
                'extra_images': [
                    _img('completed_project_images', 'completed_khalid_detail1.jpg'),
                    _img('completed_project_images', 'completed_khalid_room.jpg'),
                ],
                'is_featured': False,
            }),
        ]

        for username, cfg in showcase_defs:
            ws = self.workshops[username]
            project = CompletedProject.objects.create(
                workshop=ws,
                title=cfg['title'],
                description=cfg['description'],
                date_completed=timezone.now().date() - timedelta(days=random.randint(30, 200)),
                is_featured=cfg['is_featured'],
                is_published=True,
            )
            if cfg['main_image'].exists():
                _attach_image(project, 'main_image', cfg['main_image'])
            for extra in cfg['extra_images']:
                if extra.exists():
                    cpi = CompletedProjectImage.objects.create(project=project, caption=cfg['title'])
                    _attach_image(cpi, 'image', extra)

    # --------------------------------------------------------------------
    # Requests
    # --------------------------------------------------------------------
    def _create_requests(self):
        self.stdout.write('  Creating requests...')
        now = timezone.now()

        request_defs = [
            # (key, requester, title, desc, budget, category, days_ahead, status, ref_image)
            ('wallet', 'ahmed',
             'Custom Leather Bifold Wallet with Initials',
             ('Looking for a hand-stitched bifold wallet in dark brown vegetable-tanned '
              'leather. Embossed initials "A.O." on the front. 6 card slots.'),
             450, 'Leather Goods', 21, Request.Status.OPEN,
             _img('requests', 'ref_wallet.jpg')),

            ('calligraphy', 'noura',
             'Surah Al-Fatiha Calligraphy Frame',
             ('Surah Al-Fatiha in thuluth script, black ink on cream paper, framed in '
              'dark walnut. Roughly 50×70 cm. For my parents.'),
             1200, 'Calligraphy', 30, Request.Status.IN_REVIEW,
             _img('requests', 'ref_calligraphy.jpg')),

            ('bookshelf', 'faisal',
             'Freestanding Walnut Bookshelf',
             ('5-tier solid walnut bookshelf, around 180 cm tall, 80 cm wide. '
              'Simple modern lines, no veneer.'),
             2800, 'Woodworking', 45, Request.Status.IN_REVIEW,
             _img('requests', 'ref_bookshelf.jpg')),

            ('mugs', 'sara',
             'Set of 6 Hand-Thrown Ceramic Mugs',
             ('Matching set of 6 stoneware mugs, ~350 ml each. Matte cream glaze with '
              'a soft blue rim. Slight variation between pieces is fine.'),
             750, 'Pottery & Ceramics', 28, Request.Status.IN_REVIEW,
             _img('requests', 'ref_mugs.jpg')),

            # Closed — has an accepted proposal → Fahad's portrait contract
            ('portrait', 'ahmed',
             'Family Portrait Painting (Abstract Style)',
             ('Oil on canvas, abstract / impressionist style, of my family of 4. '
              'Roughly 80×100 cm, warm palette. Will provide reference photos.'),
             3500, 'Painting & Art', 60, Request.Status.CLOSED,
             _img('requests', 'ref_painting.jpg')),

            ('ring', 'faisal',
             'Hand-Forged Silver Ring',
             ('Solid sterling silver ring, minimal band, slight hammered texture. '
              'Size 11.'),
             600, 'Jewelry', 21, Request.Status.OPEN,
             _img('requests', 'ref_ring.jpg')),

            # Closed — Khalid's coffee table contract (currently completion_requested)
            ('coffee_table', 'sara',
             'Walnut Live-Edge Coffee Table',
             ('Single live-edge walnut slab, ~120×60 cm, on hand-forged hairpin legs. '
              'Hard-wax oil finish, no stain.'),
             3200, 'Woodworking', 40, Request.Status.CLOSED, None),

            # Closed — Laila's tote bag contract (completed)
            ('tote', 'noura',
             'Hand-Stitched Leather Tote Bag',
             ('Full-grain leather tote, vegetable-tanned, hand-stitched. Roughly 35×40 cm '
              'with a 60 cm shoulder strap. Blind-embossed monogram "N.M." on the front.'),
             1500, 'Leather Goods', 35, Request.Status.CLOSED, None),

            # Open with no proposal
            ('metal_sculpture', 'noura',
             'Decorative Metal Wall Sculpture',
             ('Forged iron or copper wall piece for an entryway. Around 80 cm wide. '
              'Organic / sunburst shape preferred.'),
             2200, 'Metalwork', 50, Request.Status.OPEN, None),

            # Time-ended
            ('tea_set', 'ahmed',
             'Pottery Tea Set',
             ('Hand-thrown pottery tea set: teapot + 4 cups. Earthy palette.'),
             900, 'Pottery & Ceramics', -5, Request.Status.TIME_ENDED, None),

            # Open
            ('thobe', 'faisal',
             'Embroidered Traditional Thobe',
             ('White thobe with subtle gold-thread embroidery around the collar and cuffs. '
              'For Eid.'),
             1100, 'Embroidery', 35, Request.Status.OPEN, None),

            # Historical closed — used only for rating seeding
            ('ceramic_bowl', 'faisal',
             'Ceramic Salad Bowl Set',
             ('Hand-thrown stoneware salad bowl with 4 matching serving bowls. '
              'Matte grey glaze.'),
             950, 'Pottery & Ceramics', -40, Request.Status.CLOSED, None),

            ('copper_panel', 'sara',
             'Forged Copper Wall Panel',
             ('Geometric copper panel, ~60×80 cm, for a hallway. Patinated finish.'),
             1800, 'Metalwork', -55, Request.Status.CLOSED, None),

            ('leather_belt', 'ahmed',
             'Hand-Stitched Leather Belt',
             ('Vegetable-tanned leather dress belt, size 34, brass buckle, saddle-stitched.'),
             350, 'Leather Goods', -30, Request.Status.CLOSED, None),
        ]

        for key, requester, title, desc, budget, cat, days_ahead, status, ref in request_defs:
            deadline = (now + timedelta(days=days_ahead)).date()
            r = Request.objects.create(
                requester=self.users[requester],
                title=title,
                description=desc,
                budget_max=Decimal(budget),
                category=self.categories[cat],
                deadline=deadline,
                status=status,
            )
            if ref and ref.exists():
                ri = RequestImage.objects.create(request=r, caption='Reference')
                _attach_image(ri, 'image', ref)
            self.requests[key] = r

    # --------------------------------------------------------------------
    # Proposals
    # --------------------------------------------------------------------
    def _create_proposals(self):
        self.stdout.write('  Creating proposals...')

        proposal_defs = [
            # (key, request_key, artisan, price, days, message, status, sample_image_filename)
            ('p_calligraphy_laila', 'calligraphy', 'laila', 1100, 14,
             ('I can do this in thuluth on Khadi paper with cream tone, framed in '
              'walnut. I have done several similar Surah Al-Fatiha pieces — see '
              'attached for an example.'),
             Proposal.Status.PENDING, 'proposal_laila_callig.jpg'),

            ('p_bookshelf_khalid', 'bookshelf', 'khalid', 2600, 30,
             ('I can build this from a single board run for matching grain. Hand-finished '
              'with hard-wax oil. Attaching a recent walnut shelf I made for reference.'),
             Proposal.Status.PENDING, 'proposal_khalid_shelf.jpg'),

            ('p_mugs_khalid', 'mugs', 'khalid', 700, 25,
             ('I throw all my mugs on the wheel; the slight variation between pieces is '
              'part of the look. Cream + soft blue rim is in my regular palette.'),
             Proposal.Status.PENDING, None),

            # Fahad's accepted proposal for the portrait → contract IN_PROGRESS
            ('p_portrait_fahad', 'portrait', 'fahad', 3400, 42,
             ('I would love to take this on. Oil on linen, warm palette, loose '
              'impressionist handling. Final piece will be varnished and ready to hang. '
              'See attached for a similar piece I did recently.'),
             Proposal.Status.ACCEPTED, 'proposal_fahad_painting.jpg'),

            # Laila's rejected bid on the same portrait (she also paints sometimes)
            ('p_portrait_laila', 'portrait', 'laila', 3800, 50,
             ('I can do this in mixed media on canvas — happy to share more sketches '
              'before starting.'),
             Proposal.Status.REJECTED, None),

            # Fahad's pending bid on the ring
            ('p_ring_fahad', 'ring', 'fahad', 580, 14,
             ('Hand-forged from a sterling silver bar, lightly hammered then polished. '
              'Will fit-check before final polish.'),
             Proposal.Status.PENDING, 'proposal_fahad_ring.jpg'),

            # Khalid's accepted proposal for the coffee table
            ('p_table_khalid', 'coffee_table', 'khalid', 3100, 35,
             ('I have a walnut slab in the workshop that would suit this perfectly — '
              'wide growth rings, live edge on both sides. Forged hairpin legs to match.'),
             Proposal.Status.ACCEPTED, None),

            # Laila's accepted proposal for the tote bag
            ('p_tote_laila', 'tote', 'laila', 1450, 28,
             ('Full-grain vegetable-tanned leather, hand-saddle-stitched with waxed '
              'thread. Edge-bevelled and burnished. Monogram blind-embossed. Sample of '
              'my past wallet work attached.'),
             Proposal.Status.ACCEPTED, 'proposal_laila_wallet.jpg'),

            # Fahad's pending bid on the metal sculpture
            ('p_metal_fahad', 'metal_sculpture', 'fahad', 2100, 30,
             ('Forged copper, organic sunburst shape, ~85 cm. I can finish with a '
              'patina or leave it polished — your call.'),
             Proposal.Status.PENDING, None),

            # Laila's withdrawn bid on the thobe
            ('p_thobe_laila', 'thobe', 'laila', 1000, 28,
             ('I can do gold-thread embroidery on the collar and cuffs.'),
             Proposal.Status.WITHDRAWN, None),

            # Khalid's pending bid on the wallet (cross-discipline — not perfect match,
            # included for status variety)
            ('p_wallet_fahad', 'wallet', 'fahad', 480, 14,
             ('I do some leatherwork on the side — happy to take this on.'),
             Proposal.Status.PENDING, None),

            # Fahad's withdrawn bid on the mugs (out of his lane)
            ('p_mugs_fahad', 'mugs', 'fahad', 800, 30,
             ('I can throw these — but realising it might be a stretch outside my '
              'usual work. Withdrawing in favour of Khalid.'),
             Proposal.Status.WITHDRAWN, None),

            # Historical accepted proposals — for rating seeding
            ('p_ceramic_khalid', 'ceramic_bowl', 'khalid', 920, 20,
             'I have thrown this style before — stoneware with a matte grey ash glaze.',
             Proposal.Status.ACCEPTED, None),

            ('p_copper_fahad', 'copper_panel', 'fahad', 1750, 25,
             'Hammered copper with a chemical patina. I can do the geometric pattern by hand.',
             Proposal.Status.ACCEPTED, None),

            ('p_belt_laila', 'leather_belt', 'laila', 340, 10,
             'Vegetable-tanned belly leather, saddle-stitched, solid brass buckle.',
             Proposal.Status.ACCEPTED, None),
        ]

        for key, req_key, artisan, price, days, msg, status, sample in proposal_defs:
            p = Proposal.objects.create(
                request=self.requests[req_key],
                artisan=self.users[artisan],
                price=Decimal(price),
                estimated_days=days,
                message=msg,
                status=status,
            )
            if sample:
                sample_path = _img('proposals', sample)
                if sample_path.exists():
                    pi = ProposalImage.objects.create(proposal=p, caption='Past work sample')
                    _attach_image(pi, 'image', sample_path)
            self.proposals[key] = p

    # --------------------------------------------------------------------
    # Contracts + progress
    # --------------------------------------------------------------------
    def _create_contracts_and_progress(self):
        self.stdout.write('  Creating contracts + progress timelines...')

        # ---- Contract 1: Fahad's portrait painting (IN_PROGRESS) ----
        c1 = Contract.objects.create(
            proposal=self.proposals['p_portrait_fahad'],
            status=Contract.Status.IN_PROGRESS,
            requester_accepted_at=timezone.now() - timedelta(days=15),
            artisan_accepted_at=timezone.now() - timedelta(days=14),
        )
        self.contracts['portrait'] = c1

        u1 = ProgressUpdate.objects.create(
            contract=c1,
            body=('Started with the under-sketch on linen. Proportions are locked in. '
                  'Will lay in the warm underpainting next.'),
        )
        self._attach_progress_image(u1, _img('progress', 'progress_portrait_sketch.jpg'),
                                     'Initial sketch on linen')

        ProgressComment.objects.create(
            update=u1, author=self.users['ahmed'],
            body='Looks great! Can you make the eyes a touch larger? More like the reference.',
        )

        u2 = ProgressUpdate.objects.create(
            contract=c1,
            body=('About 70% there. Warm palette is laid in, faces are starting to read. '
                  'Will keep going on the background.'),
        )
        self._attach_progress_image(u2, _img('progress', 'progress_portrait_wip.jpg'),
                                     'In progress — 70% complete')

        # Requester comment with an image attached
        comment_with_img = ProgressComment.objects.create(
            update=u2, author=self.users['ahmed'],
            body='Love the warm tones. If possible, can the background match this dusty rose?',
        )
        cci = ProgressCommentImage.objects.create(comment=comment_with_img, caption='Colour reference')
        _attach_image(cci, 'image', _img('progress_comments', 'comment_color_swatch.jpg'))

        # ---- Contract 2: Khalid's coffee table (COMPLETION_REQUESTED, with prior rejection) ----
        c2 = Contract.objects.create(
            proposal=self.proposals['p_table_khalid'],
            status=Contract.Status.COMPLETION_REQUESTED,
            requester_accepted_at=timezone.now() - timedelta(days=40),
            artisan_accepted_at=timezone.now() - timedelta(days=39),
        )
        self.contracts['coffee_table'] = c2

        u3 = ProgressUpdate.objects.create(
            contract=c2,
            body=('Walnut slab is in the shop. Going to rough-cut and let it acclimate '
                  'for a few days before the final flattening.'),
        )
        self._attach_progress_image(u3, _img('progress', 'progress_table_slab.jpg'),
                                     'Raw walnut slab')

        # Requester comment with photo of the room
        c2_comment = ProgressComment.objects.create(
            update=u3, author=self.users['sara'],
            body='Here is the room it will go in — can you confirm the height is 45 cm?',
        )
        cci2 = ProgressCommentImage.objects.create(comment=c2_comment, caption='Room photo')
        _attach_image(cci2, 'image', _img('progress_comments', 'comment_room_photo.jpg'))

        # First completion request (which got rejected)
        e1 = ContractEvent.objects.create(
            contract=c2,
            event_type=ContractEvent.EventType.COMPLETION_REQUESTED,
            actor=self.users['khalid'],
            message='Table is finished and ready for delivery. Final shot attached.',
        )
        ev_img1 = ContractEventImage.objects.create(event=e1, caption='Finished — first attempt')
        _attach_image(ev_img1, 'image', _img('progress_events', 'event_complete_proof.jpg'))

        # Requester sent it back
        e2 = ContractEvent.objects.create(
            contract=c2,
            event_type=ContractEvent.EventType.COMPLETION_REJECTED,
            actor=self.users['sara'],
            message=('Looks great overall, but one of the hairpin legs is sitting a couple '
                     'of mm off — see attached. Can you level it before I confirm?'),
        )
        ev_img2 = ContractEventImage.objects.create(event=e2, caption='Leg level issue')
        _attach_image(ev_img2, 'image', _img('progress_events', 'event_reject_issue.jpg'))

        # Khalid fixed it and posted a new update
        u4 = ProgressUpdate.objects.create(
            contract=c2,
            body='Re-levelled all four legs and re-finished the underside. Should be true now.',
        )
        self._attach_progress_image(u4, _img('progress', 'progress_table_legs.jpg'),
                                     'Legs re-levelled')

        # Second completion request (currently awaiting confirmation)
        e3 = ContractEvent.objects.create(
            contract=c2,
            event_type=ContractEvent.EventType.COMPLETION_REQUESTED,
            actor=self.users['khalid'],
            message='Packaged and ready for delivery — please confirm when you can.',
        )
        ev_img3 = ContractEventImage.objects.create(event=e3, caption='Packed for delivery')
        _attach_image(ev_img3, 'image', _img('progress_events', 'event_complete_packaging.jpg'))

        # ---- Contract 3: Laila's tote bag (COMPLETED) ----
        c3 = Contract.objects.create(
            proposal=self.proposals['p_tote_laila'],
            status=Contract.Status.COMPLETED,
            requester_accepted_at=timezone.now() - timedelta(days=35),
            artisan_accepted_at=timezone.now() - timedelta(days=34),
            completed_at=timezone.now() - timedelta(days=3),
        )
        self.contracts['tote'] = c3

        u5 = ProgressUpdate.objects.create(
            contract=c3,
            body='Cut the panels and bevelled all the edges. Ready to stitch.',
        )
        self._attach_progress_image(u5, _img('progress', 'progress_bag_cut.jpg'),
                                     'Panels cut and bevelled')

        u6 = ProgressUpdate.objects.create(
            contract=c3,
            body='Hand-saddle-stitching the body. Slow but worth it — this stitch holds even if a thread breaks.',
        )
        self._attach_progress_image(u6, _img('progress', 'progress_bag_stitch.jpg'),
                                     'Saddle-stitching in progress')

        # Requester comment with an inspiration image
        c3_comment = ProgressComment.objects.create(
            update=u6, author=self.users['noura'],
            body='Beautiful! Can the strap stitching match this colour exactly?',
        )
        cci3 = ProgressCommentImage.objects.create(comment=c3_comment, caption='Stitch colour reference')
        _attach_image(cci3, 'image', _img('progress_comments', 'comment_inspiration.jpg'))

        u7 = ProgressUpdate.objects.create(
            contract=c3,
            body='All done! Conditioned, polished, and ready for handover.',
        )
        self._attach_progress_image(u7, _img('progress', 'progress_bag_final.jpg'),
                                     'Finished tote')

        # Completion request + confirmation
        ContractEvent.objects.create(
            contract=c3,
            event_type=ContractEvent.EventType.COMPLETION_REQUESTED,
            actor=self.users['laila'],
            message='Tote is finished and conditioned. Ready when you are.',
        )

        ContractEvent.objects.create(
            contract=c3,
            event_type=ContractEvent.EventType.COMPLETED,
            actor=self.users['noura'],
            message='Received and absolutely love it. Confirming completion.',
        )

        # ---- Historical contracts (no progress detail — used for rating seeding) ----
        c4 = Contract.objects.create(
            proposal=self.proposals['p_ceramic_khalid'],
            status=Contract.Status.COMPLETED,
            requester_accepted_at=timezone.now() - timedelta(days=45),
            artisan_accepted_at=timezone.now() - timedelta(days=44),
            completed_at=timezone.now() - timedelta(days=30),
        )
        self.contracts['ceramic_bowl'] = c4

        c5 = Contract.objects.create(
            proposal=self.proposals['p_copper_fahad'],
            status=Contract.Status.COMPLETED,
            requester_accepted_at=timezone.now() - timedelta(days=60),
            artisan_accepted_at=timezone.now() - timedelta(days=59),
            completed_at=timezone.now() - timedelta(days=45),
        )
        self.contracts['copper_panel'] = c5

        c6 = Contract.objects.create(
            proposal=self.proposals['p_belt_laila'],
            status=Contract.Status.COMPLETED,
            requester_accepted_at=timezone.now() - timedelta(days=35),
            artisan_accepted_at=timezone.now() - timedelta(days=34),
            completed_at=timezone.now() - timedelta(days=20),
        )
        self.contracts['leather_belt'] = c6

    def _attach_progress_image(self, update, image_path, caption):
        if image_path.exists():
            pi = ProgressImage.objects.create(update=update, caption=caption)
            _attach_image(pi, 'image', image_path)

    # --------------------------------------------------------------------
    # Conversations + messages
    # --------------------------------------------------------------------
    def _create_conversations(self):
        self.stdout.write('  Creating conversations + messages...')

        # Each accepted proposal gets a conversation.
        convo_defs = [
            ('p_portrait_fahad', 'ahmed', 'fahad', [
                ('ahmed', 'Hi Fahad! Excited to start. I will send the family photos shortly.', None),
                ('fahad',  'Perfect. Any preference on background tone — warmer or cooler?', None),
                ('ahmed', 'Warm. Something like sunset.', None),
                ('fahad',  'Got it. Sending a quick palette test for approval.',
                          _img('conversation_images', 'chat_color_question.jpg')),
                ('ahmed', 'Love it. Go for it!', None),
            ]),
            ('p_table_khalid', 'sara', 'khalid', [
                ('sara',    'Hi Khalid — quick question, can you fit the slab so the live edge faces the sofa?', None),
                ('khalid',  'Yes, no problem. I will orient it that way before cutting.', None),
                ('khalid',  'Here is a rough mock-up of the orientation.',
                            _img('conversation_images', 'chat_quick_ref.jpg')),
                ('sara',    'Perfect, thank you!', None),
                ('khalid',  'Will update once the slab is rough-cut.', None),
            ]),
            ('p_tote_laila', 'noura', 'laila', [
                ('noura',  'Hi Laila! Just confirming the strap length — 60 cm shoulder length is good?', None),
                ('laila',  'Yes, 60 cm is right for shoulder carry. Want me to leave room for adjustment?', None),
                ('noura',  'No, fixed at 60 is fine. Excited to see it come together.', None),
                ('laila',  'Quick peek — first row of stitching is in.',
                           _img('conversation_images', 'chat_progress_peek.jpg')),
                ('noura',  'Beautiful work!', None),
            ]),
        ]

        for proposal_key, requester, artisan, messages in convo_defs:
            proposal = self.proposals[proposal_key]
            conv = Conversation.objects.create(
                proposal=proposal,
                requester=self.users[requester],
                artisan=self.users[artisan],
            )
            for sender, body, image_path in messages:
                msg = Message.objects.create(
                    conversation=conv,
                    sender=self.users[sender],
                    body=body,
                    is_read=True,
                )
                if image_path and image_path.exists():
                    with open(image_path, 'rb') as f:
                        msg.image.save(image_path.name, File(f), save=True)

    # --------------------------------------------------------------------
    # Reviews  (signals auto-recalculate ArtisanProfile.average_rating)
    # --------------------------------------------------------------------
    def _create_reviews(self):
        self.stdout.write('  Creating reviews...')

        # Laila — tote (5★) + leather belt (4★)  →  avg 4.5
        Review.objects.create(
            request=self.requests['tote'],
            reviews_given=self.users['noura'],
            reviews_received=self.users['laila'],
            rating=5,
            comment=('Absolutely beautiful work. The stitching is even, the monogram is perfect, '
                     'and Laila kept me in the loop the whole way through. Will commission again.'),
        )
        Review.objects.create(
            request=self.requests['leather_belt'],
            reviews_given=self.users['ahmed'],
            reviews_received=self.users['laila'],
            rating=4,
            comment='Great quality leather and clean stitching. Delivery was on time. Very happy.',
        )

        # Khalid — ceramic bowl set (4★)  →  avg 4.0
        Review.objects.create(
            request=self.requests['ceramic_bowl'],
            reviews_given=self.users['faisal'],
            reviews_received=self.users['khalid'],
            rating=4,
            comment=('Solid craftsmanship. The glaze colour was slightly off from what I expected, '
                     'but the throwing quality and weight of the bowls is excellent.'),
        )

        # Fahad — copper panel (5★)  →  avg 5.0
        Review.objects.create(
            request=self.requests['copper_panel'],
            reviews_given=self.users['sara'],
            reviews_received=self.users['fahad'],
            rating=5,
            comment=('Stunning piece. The patina is exactly what I asked for and it arrived '
                     'perfectly packaged. Fahad is a true craftsman.'),
        )

    # --------------------------------------------------------------------
    # Invitations
    # --------------------------------------------------------------------
    def _create_invitations(self):
        self.stdout.write('  Creating invitations...')

        # Faisal invites Khalid to bookshelf → PROPOSED (Khalid already bid)
        Invitation.objects.create(
            request=self.requests['bookshelf'],
            artisan=self.users['khalid'],
            status=Invitation.Status.PROPOSED,
            viewed_at=timezone.now() - timedelta(days=2),
        )
        # Noura invites Fahad to metal_sculpture → PROPOSED (Fahad already bid)
        Invitation.objects.create(
            request=self.requests['metal_sculpture'],
            artisan=self.users['fahad'],
            status=Invitation.Status.PROPOSED,
            viewed_at=timezone.now() - timedelta(days=1),
        )
        # Ahmed invites Laila to ring → VIEWED (she looked but didn't bid)
        Invitation.objects.create(
            request=self.requests['ring'],
            artisan=self.users['laila'],
            status=Invitation.Status.VIEWED,
            viewed_at=timezone.now() - timedelta(hours=6),
        )
        # Sara invites Khalid to mugs — PENDING (not yet viewed)
        Invitation.objects.create(
            request=self.requests['mugs'],
            artisan=self.users['khalid'],
            status=Invitation.Status.PENDING,
        )

    # --------------------------------------------------------------------
    # Notification preferences
    # --------------------------------------------------------------------
    def _create_notification_preferences(self):
        self.stdout.write('  Creating notification preferences...')
        for username in DEMO_USERNAMES:
            u = self.users[username]
            NotificationPreference.objects.get_or_create(user=u)
        # Demo a "some toggles off" user — Faisal turns off email notifications
        # for proposal_received and message_received (just to show the settings page works).
        faisal_prefs = NotificationPreference.objects.get(user=self.users['faisal'])
        faisal_prefs.email_proposal_received = False
        faisal_prefs.email_message_received = False
        faisal_prefs.save(update_fields=['email_proposal_received', 'email_message_received'])

    # --------------------------------------------------------------------
    # Notifications  (mix of read / unread to populate the bell)
    # --------------------------------------------------------------------
    def _create_notifications(self):
        self.stdout.write('  Creating notifications...')
        NT = Notification.NotifType

        def n(recipient, notif_type, title, body='', is_read=True):
            Notification.objects.create(
                recipient=self.users[recipient],
                notif_type=notif_type,
                title=title,
                body=body,
                is_read=is_read,
            )

        # --- Ahmed (requester) ---
        n('ahmed', NT.PROPOSAL_RECEIVED, 'New proposal on your wallet request',
          'Fahad submitted a proposal for SAR 480.', is_read=False)
        n('ahmed', NT.PROPOSAL_RECEIVED, 'New proposal on your portrait request',
          'Fahad submitted a proposal for SAR 3,400.', is_read=True)
        n('ahmed', NT.PROPOSAL_ACCEPTED, 'Your portrait proposal was accepted',
          "You accepted Fahad's proposal. The project is now underway.", is_read=True)
        n('ahmed', NT.PROGRESS_UPDATE, 'Fahad posted a progress update',
          'Initial sketch on linen — proportions locked in.', is_read=True)
        n('ahmed', NT.PROGRESS_UPDATE, 'Fahad posted another update',
          '70% complete — warm palette is in, faces are reading well.', is_read=False)

        # --- Noura (requester) ---
        n('noura', NT.PROPOSAL_RECEIVED, 'New proposal on your calligraphy request',
          'Laila submitted a proposal for SAR 1,100.', is_read=False)
        n('noura', NT.COMPLETION_CONFIRMED, 'Your tote bag project is complete!',
          "You confirmed completion of Laila's tote bag.", is_read=True)

        # --- Faisal (requester) ---
        n('faisal', NT.PROPOSAL_RECEIVED, 'New proposal on your bookshelf request',
          'Khalid submitted a proposal for SAR 2,600.', is_read=False)
        n('faisal', NT.INVITATION_RECEIVED, 'You were invited to a project',
          'Check your invitations for a new request.', is_read=True)

        # --- Sara (requester) ---
        n('sara', NT.PROPOSAL_RECEIVED, 'New proposal on your mugs request',
          'Khalid submitted a proposal for SAR 700.', is_read=False)
        n('sara', NT.COMPLETION_REQUESTED, 'Khalid is requesting completion',
          'Please review and confirm the coffee table delivery.', is_read=False)

        # --- Laila (artisan) ---
        n('laila', NT.PROPOSAL_ACCEPTED, 'Your tote bag proposal was accepted!',
          'Noura accepted your proposal for SAR 1,450.', is_read=True)
        n('laila', NT.COMMENT_ADDED, 'Noura commented on your progress update',
          'Can the strap stitching match this colour exactly?', is_read=True)
        n('laila', NT.INVITATION_RECEIVED, 'You were invited to a ring project',
          'Ahmed invited you to look at a leather belt request.', is_read=False)

        # --- Khalid (artisan) ---
        n('khalid', NT.PROPOSAL_ACCEPTED, 'Your coffee table proposal was accepted!',
          'Sara accepted your proposal for SAR 3,100.', is_read=True)
        n('khalid', NT.COMPLETION_REJECTED, 'Sara sent back your completion request',
          'One hairpin leg is sitting a couple of mm off — please level before confirming.',
          is_read=True)
        n('khalid', NT.INVITATION_RECEIVED, 'You were invited to a bookshelf project',
          'Faisal invited you to look at his walnut bookshelf request.', is_read=True)

        # --- Fahad (artisan) ---
        n('fahad', NT.PROPOSAL_ACCEPTED, 'Your portrait proposal was accepted!',
          'Ahmed accepted your proposal for SAR 3,400.', is_read=True)
        n('fahad', NT.COMMENT_ADDED, 'Ahmed commented on your progress update',
          'Love the warm tones — can the background match this dusty rose?', is_read=False)
        n('fahad', NT.INVITATION_RECEIVED, 'You were invited to a metal sculpture project',
          'Noura invited you to look at her decorative wall sculpture request.', is_read=True)

        # --- Staff ---
        n('staff_admin', NT.REPORT_RECEIVED, 'New report submitted',
          'Sara reported a review as spam.', is_read=False)
        n('staff_admin', NT.DISPUTE_RECEIVED, 'New dispute opened',
          'Sara opened a quality dispute on the coffee table contract.', is_read=False)

    # --------------------------------------------------------------------
    # Payment methods  (Stripe test card 4242424242424242)
    # --------------------------------------------------------------------
    def _create_payment_methods(self):
        self.stdout.write('  Creating payment methods...')
        # Seed a saved Visa test card for every requester and artisan.
        # These use fake Stripe IDs — real charges require the test PaymentIntent flow.
        users_to_seed = ['ahmed', 'noura', 'faisal', 'sara', 'laila', 'khalid', 'fahad']
        for username in users_to_seed:
            u = self.users[username]
            cus_id = f'cus_demo_{username}'
            pm_id  = f'pm_demo_{username}'
            StripeCustomer.objects.create(
                user=u,
                stripe_customer_id=cus_id,
            )
            PaymentMethod.objects.create(
                user=u,
                stripe_customer_id=cus_id,
                stripe_payment_method_id=pm_id,
                brand='visa',
                last4='4242',
                exp_month=12,
                exp_year=2028,
                is_default=True,
            )

    # --------------------------------------------------------------------
    # Optional: one open dispute
    # --------------------------------------------------------------------
    def _create_dispute(self):
        self.stdout.write('  Creating one open dispute...')
        contract = self.contracts['coffee_table']  # the one in COMPLETION_REQUESTED
        dispute = Dispute.objects.create(
            contract=contract,
            opened_by=self.users['sara'],
            reason=Dispute.Reason.QUALITY,
            description=('After the re-leveling, the table is closer but the finish on the '
                         'underside is uneven. I would like staff to weigh in before I confirm.'),
            status=Dispute.Status.OPEN,
        )

        # Two messages from the requester side (staff <-> requester channel)
        DisputeMessage.objects.create(
            dispute=dispute,
            party=self.users['sara'],
            sender=self.users['sara'],
            body='Attaching a close-up of what I am seeing.',
        )
        msg_with_img = DisputeMessage.objects.create(
            dispute=dispute,
            party=self.users['sara'],
            sender=self.users['sara'],
            body='Here it is — does this look acceptable to you?',
        )
        img_path = _img('disputes', 'dispute_evidence_damage.jpg')
        if img_path.exists():
            with open(img_path, 'rb') as f:
                msg_with_img.image.save(img_path.name, File(f), save=True)

        # One message from the artisan side (staff <-> artisan channel)
        artisan_msg = DisputeMessage.objects.create(
            dispute=dispute,
            party=self.users['khalid'],
            sender=self.users['khalid'],
            body=('That spot is from the bench during finishing — I am happy to re-buff and '
                  're-oil it before final handover. Attaching how it was packed.'),
        )
        img_path2 = _img('disputes', 'dispute_evidence_packed.jpg')
        if img_path2.exists():
            with open(img_path2, 'rb') as f:
                artisan_msg.image.save(img_path2.name, File(f), save=True)

        # Staff reply, marking it In Review
        DisputeMessage.objects.create(
            dispute=dispute,
            party=self.users['sara'],
            sender=self.users['staff_admin'],
            body='Reviewing now — will get back to both of you within 24 hours.',
        )
        dispute.status = Dispute.Status.IN_REVIEW
        dispute.save(update_fields=['status'])

    # --------------------------------------------------------------------
    # Optional: a couple of reports
    # --------------------------------------------------------------------
    def _create_reports(self):
        self.stdout.write('  Creating sample reports...')
        # 1. Sara reports the (only) review for being "too generic" — pending
        review = Review.objects.first()
        if review:
            Report.objects.create(
                reporter=self.users['sara'],
                content_type=Report.ContentType.REVIEW,
                reported_review=review,
                reason=Report.Reason.SPAM,
                details='This review reads like it was copy-pasted. Worth checking.',
                status=Report.Status.PENDING,
            )

        # 2. Faisal reports the time-ended tea-set request as inappropriate — already dismissed
        Report.objects.create(
            reporter=self.users['faisal'],
            content_type=Report.ContentType.REQUEST,
            reported_request=self.requests['tea_set'],
            reason=Report.Reason.INAPPROPRIATE,
            details='Title seems off-topic for this category.',
            status=Report.Status.DISMISSED,
            resolution_note='Reviewed — request title is on-topic.',
            reviewed_by=self.users['staff_admin'],
            reviewed_at=timezone.now() - timedelta(days=1),
        )
