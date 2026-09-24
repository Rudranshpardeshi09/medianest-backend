"""
Load the content the site already shows into the database.

The point is parity: after seeding, the page must render exactly what it
rendered before anything was made dynamic. Every string here is copied
verbatim from the frontend components, not paraphrased.

Safe to run more than once -- it updates in place and never duplicates. It
will not overwrite an edit made in the admin unless `--force` is given, so
running it again after go-live cannot quietly undo someone's work.
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from content.models import (
    AboutContent,
    AboutPillar,
    Client,
    ClientsContent,
    ContactContent,
    FooterContent,
    Discipline,
    DisciplineImage,
    DisciplineVideo,
    Person,
    PersonLine,
    PersonSocial,
    Reason,
    Service,
    SiteSettings,
    SocialLink,
    TeamContent,
    Testimonial,
    WhyChooseContent,
)

# Copied from src/components/Services.jsx SERVICES.
SERVICES = [
    {
        "title": "Photography & Brand Visual Presence",
        "short_label": "Photography",
        "body": (
            "Professional photography that highlights the unique aspects of "
            "your brand — considered, lit and directed to carry a visual identity."
        ),
        "tags": "Editorial, Product, Sports, Profiling",
        "image": "PHOTOGRAPHY-AND-BRAND-1.webp",
    },
    {
        "title": "Cinematography & Quality Production",
        "short_label": "Cinematography",
        "body": (
            "Creative storytelling through high-quality, engaging film content "
            "— from concept and shoot through to the finished cut."
        ),
        "tags": "Brand films, Documentary, Live stream, Post",
        "image": "CINEMATOGRAPHY-PRODUCTION-1.webp",
    },
    {
        "title": "Brand Image Strategy & Consultation",
        "short_label": "Brand Strategy",
        "body": (
            "Tailored guidance to refine and align your brand image with its "
            "business goals, across every surface it appears on."
        ),
        "tags": "Positioning, Art direction, Content strategy, Rollout",
        "image": "BRAND-IMAGE-STRATEGY-1.webp",
    },
]

# Copied from src/components/Services.jsx MORE. Names only on the page.
SERVICE_STRIP = [
    "Interviews",
    "Live Streaming",
    "Video Editing",
    "Graphic Design",
    "Events",
    "Digital Marketing",
]

# Copied from src/components/About.jsx PILLARS.
PILLARS = [
    {
        "title": "Holistic Approach",
        "body": (
            "We treat brand image as one system, focusing on visual and "
            "tangible content that drives engagement and trust."
        ),
        "is_wide": False,
    },
    {
        "title": "Tailored Services",
        "body": (
            "High-quality film production, professional photography and "
            "content strategy, shaped to position brands as industry leaders."
        ),
        "is_wide": False,
    },
    {
        "title": "Extensive Networking",
        "body": (
            "Deep professional experience and rooted networking opportunities, "
            "so every engagement carries further than the work itself."
        ),
        "is_wide": True,
    },
]

ABOUT_FIGURE = "INTERVIEW.webp"

# Copied from src/components/WhyChoose.jsx REASONS. The figures each reason
# used to carry are deliberately absent -- see the Reason model docstring.
REASONS = [
    {
        "label": "Proven Expertise",
        "body": (
            "A team of experts with over 5+ years of hands-on experience in "
            "brand image management."
        ),
    },
    {
        "label": "Comprehensive Services",
        "body": (
            "From strategy to execution, we provide a full suite of services "
            "designed to enhance your brand visibility."
        ),
    },
    {
        "label": "Industry Networking",
        "body": (
            "With our robust network of industry contacts, we offer unique "
            "opportunities for collaboration and growth."
        ),
    },
    {
        "label": "Client-Centric Approach",
        "body": (
            "We tailor our services to the specific needs of each client, "
            "ensuring every project is personalized and effective."
        ),
    },
]

# Copied from src/components/Footer.jsx SOCIAL. WhatsApp carries no URL:
# the footer builds it from the phone number in Site settings.
SOCIAL = [
    ("facebook", "https://www.facebook.com/medianest2024"),
    ("instagram", "https://www.instagram.com/medianest.official/"),
    ("whatsapp", ""),
    ("youtube", "https://youtube.com/@medianesttv?feature=shared"),
    ("linkedin", "https://www.linkedin.com/company/104838310/"),
]

# Copied from src/components/Clients.jsx CLIENTS. `sector` is what the
# organisation is, not a claim about the work.
CLIENTS = [
    ("IBSF", "International Federation", "IBSF-Logo.webp", "https://www.instagram.com/ibsf.media/"),
    ("ACBS", "Asian Confederation", "ACBS-LOGO.webp", "https://www.instagram.com/acbsmedia/"),
    ("PABSA", "Pan American Association", "PABSA-LOGO.webp", "https://www.instagram.com/pabsaofficial/"),
    ("OGQ", "Olympic Gold Quest", "OGQ_logo_dark.webp", "https://www.ogq.org"),
    ("Indian Oil", "Energy", "indianoil.webp", "https://iocl.com"),
    ("Oil India", "Energy", "OIL.webp", "https://www.oil-india.com"),
    ("PSPB", "Sports Promotion Board", "PSPB-Logo-White-Background.webp", "https://www.instagram.com/pspblive/"),
    ("Cue Sports India", "National Federation", "CSI-Logo-Round-1.webp", "https://www.instagram.com/cuesportsindia/"),
]
CLIENTS = [dict(zip(("name", "sector", "logo", "url"), row)) for row in CLIENTS]

# Copied from src/components/Testimonials.jsx QUOTES.
TESTIMONIALS = [
    {
        "quote": (
            "MediaNest helps power PABSA, bringing billiards and snooker to the "
            "forefront in the Americas. We extend best wishes for their continued "
            "growth and success."
        ),
        "name": "Ajeya Prabhakar",
        "role": "President, Pan American Billiards & Snooker Association",
        "photo": "ajeya-1.webp",
    },
    {
        "quote": (
            "I extend my best wishes to the Media Nest team for continued success "
            "and creative excellence. As you lead the way in brand image management, "
            "may your innovative ideas keep inspiring brilliance and leaving a "
            "lasting impact on the brands you collaborate with."
        ),
        "name": "SPS Kalra",
        "role": "Fashion & Cinematic Photographer",
        "photo": "spskalra.webp",
    },
]

# Copied from src/components/Team.jsx FOUNDERS. The icon classes are not
# carried over -- the platform key is stored and the frontend owns the class.
#
# Both photos are 375x560 against a frame that renders 460x613 and wants
# 920x1226 on a 2x screen, so they are already being upscaled on the live
# site. Seeded as they are, deliberately: the page must not change. The
# admin's crop preview says how short each one is.
PEOPLE = [
    {
        "first_name": "Aditi",
        "last_name": "Singh",
        "role": "Managing Partner",
        "photo": "ADITI-MAM-1.webp",
        "lines": ["Still Life & Sports Photographer", "Artist & Poet"],
        "social": [
            ("instagram", "https://www.instagram.com/aditisinghphotography"),
            ("youtube", "https://youtube.com/@aditisinghphotography"),
        ],
    },
    {
        "first_name": "Vivek",
        "last_name": "Pathak",
        "role": "Managing Partner",
        "photo": "VIVEK-SIR-2.webp",
        "lines": [
            "Former Athlete",
            "Sports Administrator",
            "Sports & Profiling Photographer",
        ],
        "social": [
            ("instagram", "https://www.instagram.com/pafcoms"),
            ("linkedin", "https://www.linkedin.com/in/vivek-pathak-5257312a"),
        ],
    },
]

# Copied from src/lib/work.js WORK, in grid order. A tile carries either
# films or stills, never both.
DISCIPLINES = [
    {
        "name": "Photography", "meta_label": "Stills", "cover": "photography.webp",
        "images": [
            ("gal-photography-1.webp", "Sports photography by Media Nest"),
            ("gal-photography-2.webp", "Sports photography by Media Nest"),
            ("gal-photography-3.webp", "Sports photography by Media Nest"),
        ],
    },
    {
        "name": "Cinematography", "meta_label": "Motion", "cover": "cinematography_main.webp",
        "videos": [("Cldlv3d36Jc", "Cinematography")],
    },
    {
        "name": "Interview", "meta_label": "Voice", "cover": "INTERVIEW.webp",
        "videos": [("tz4CPFl_YfU", "Interviews")],
    },
    {
        "name": "Live Stream", "meta_label": "Broadcast", "cover": "LIVE-STREAM.webp",
        "videos": [("EDtsbsAljU8", "Live Stream")],
    },
    {
        "name": "Event", "meta_label": "Coverage", "cover": "EVENT.webp",
        "videos": [("fU1PKUO0FyI", "Event")],
    },
    {
        "name": "Graphic Design", "meta_label": "Identity", "cover": "graphic-1.webp",
        "images": [
            ("gal-graphic-1.webp", "Graphic design work by Media Nest"),
            ("gal-graphic-2.webp", "Graphic design work by Media Nest"),
        ],
    },
    {
        "name": "Video Edit", "meta_label": "Post", "cover": "video-edit.webp",
        "videos": [("wGwSSFfbcEs", "Football Teaser"), ("kvHo80ZIUxU", "Hockey Teaser")],
    },
    {
        "name": "Digital Marketing", "meta_label": "Reach", "cover": "new_DIGITAL-MARKETING.webp",
        "images": [
            ("gal-digital-1.webp", "Digital marketing work by Media Nest"),
            ("gal-digital-2.webp", "Digital marketing work by Media Nest"),
        ],
    },
]


def _clear(queryset, *image_fields):
    """
    Delete rows and the files they own.

    Django stopped removing a FileField's file when its row goes, so a re-seed
    leaves the old images behind and the next one saves alongside them under a
    suffixed name -- `ajeya-1_QJU8Hly.webp` next to `ajeya-1.webp`. Harmless
    once, but it accumulates every time `--force` is used.
    """
    for row in queryset:
        for field in image_fields:
            f = getattr(row, field, None)
            if f:
                f.delete(save=False)
    queryset.delete()


class Command(BaseCommand):
    help = "Seed the database with the content the frontend currently hardcodes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--media-from",
            default="../medianest/public/media",
            help=(
                "Where the frontend's images live, so the seed can copy them "
                "in. Relative paths resolve against the backend directory."
            ),
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite rows that already exist. Without this, existing rows are left alone.",
        )

    def handle(self, *args, **options):
        force = options["force"]
        media_dir = Path(options["media_from"])
        if not media_dir.is_absolute():
            media_dir = (Path(settings.BASE_DIR) / media_dir).resolve()

        self._seed_settings(force)
        self._seed_about(force, media_dir)
        self._seed_pillars(force)
        self._seed_services(force, media_dir)
        self._seed_disciplines(force, media_dir)
        self._seed_reasons(force)
        self._seed_people(force, media_dir)
        self._seed_testimonials(force, media_dir)
        self._seed_clients(force, media_dir)
        ContactContent.load()
        self._seed_footer(force)

        self.stdout.write(self.style.SUCCESS("\nSeed complete."))

    # ------------------------------------------------------------------
    def _seed_settings(self, force):
        obj = SiteSettings.load()
        # The model defaults already carry the live values, so a fresh row is
        # correct as created. Nothing to overwrite unless asked.
        if force:
            for field, value in SiteSettings().__dict__.items():
                if field.startswith("_") or field in {"id", "updated_at"}:
                    continue
                setattr(obj, field, value)
            obj.save()
        self.stdout.write(
            f"  site settings   : {obj.years_of_practice} · "
            f"{obj.discipline_count}/{obj.discipline_count_word} · "
            f"{obj.hours_compact}/{obj.hours_spaced} · {obj.coverage}"
        )

    def _seed_about(self, force, media_dir):
        obj = AboutContent.load()
        if force:
            fresh = AboutContent()
            obj.heading = fresh.heading
            obj.description = fresh.description
            obj.figure_alt = fresh.figure_alt
            obj.focal_x, obj.focal_y = fresh.focal_x, fresh.focal_y

        if not obj.figure or force:
            source = media_dir / ABOUT_FIGURE
            if source.exists():
                with source.open("rb") as fh:
                    obj.figure.save(ABOUT_FIGURE, File(fh), save=False)
                self.stdout.write(f"  about figure    : copied {source.name}")
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"  about figure    : not found at {source}\n"
                        f"                    pass --media-from <path to the frontend's public/media>"
                    )
                )
        obj.save()
        self.stdout.write(f"  about content   : {obj.heading[:46]}...")

    def _seed_pillars(self, force):
        if AboutPillar.objects.exists() and not force:
            self.stdout.write(
                f"  about pillars   : {AboutPillar.objects.count()} already present, left alone"
            )
            return
        AboutPillar.objects.all().delete()
        for i, data in enumerate(PILLARS):
            AboutPillar.objects.create(order=i, **data)
        self.stdout.write(f"  about pillars   : {len(PILLARS)} created")

    def _seed_services(self, force, media_dir):
        if Service.objects.exists() and not force:
            self.stdout.write(
                f"  services        : {Service.objects.count()} already present, left alone"
            )
            return
        _clear(Service.objects.all(), "image")

        missing = []
        for i, data in enumerate(SERVICES):
            filename = data.pop("image")
            svc = Service(order=i, is_featured=True, **data)
            source = media_dir / filename
            if source.exists():
                with source.open("rb") as fh:
                    svc.image.save(filename, File(fh), save=False)
            else:
                missing.append(filename)
            svc.save()
            data["image"] = filename  # keep the module-level list reusable

        # The strip carries names only, so no body, image or tags.
        for j, name in enumerate(SERVICE_STRIP):
            Service.objects.create(title=name, is_featured=False, order=len(SERVICES) + j)

        self.stdout.write(
            f"  services        : {len(SERVICES)} featured + {len(SERVICE_STRIP)} in the strip"
        )
        if missing:
            self.stdout.write(
                self.style.WARNING(f"                    images not found: {', '.join(missing)}")
            )

    def _seed_disciplines(self, force, media_dir):
        if Discipline.objects.exists() and not force:
            self.stdout.write(
                f"  disciplines     : {Discipline.objects.count()} already present, left alone"
            )
            return
        _clear(DisciplineImage.objects.all(), "image")
        _clear(Discipline.objects.all(), "cover")

        missing = []
        films = stills = 0
        for i, data in enumerate(DISCIPLINES):
            tile = Discipline(
                name=data["name"],
                meta_label=data["meta_label"],
                order=i,
                is_published=True,
            )
            source = media_dir / data["cover"]
            if source.exists():
                with source.open("rb") as fh:
                    tile.cover.save(data["cover"], File(fh), save=False)
            else:
                missing.append(data["cover"])
            tile.save()

            for j, (youtube_id, title) in enumerate(data.get("videos", [])):
                DisciplineVideo.objects.create(
                    discipline=tile, youtube_id=youtube_id, title=title, order=j
                )
                films += 1

            for j, (filename, alt) in enumerate(data.get("images", [])):
                shot = DisciplineImage(discipline=tile, alt=alt, order=j)
                source = media_dir / filename
                if source.exists():
                    with source.open("rb") as fh:
                        shot.image.save(filename, File(fh), save=False)
                    shot.save()
                    stills += 1
                else:
                    missing.append(filename)

        shown = min(len(DISCIPLINES), Discipline.VISIBLE_TILES)
        self.stdout.write(
            f"  disciplines     : {len(DISCIPLINES)} tiles ({shown} on the page) "
            f"holding {films} films + {stills} stills"
        )
        if missing:
            self.stdout.write(
                self.style.WARNING(f"                    images not found: {', '.join(missing)}")
            )

    def _seed_reasons(self, force):
        if Reason.objects.exists() and not force:
            self.stdout.write(
                f"  reasons         : {Reason.objects.count()} already present, left alone"
            )
            return
        Reason.objects.all().delete()
        for i, data in enumerate(REASONS):
            Reason.objects.create(order=i, **data)
        WhyChooseContent.load()  # default heading carries {count}
        self.stdout.write(f"  reasons         : {len(REASONS)} created")

    def _seed_people(self, force, media_dir):
        if Person.objects.exists() and not force:
            self.stdout.write(
                f"  people          : {Person.objects.count()} already present, left alone"
            )
            return
        _clear(Person.objects.all(), "photo")

        missing = []
        for i, data in enumerate(PEOPLE):
            person = Person(
                first_name=data["first_name"],
                last_name=data["last_name"],
                role=data["role"],
                order=i,
            )
            source = media_dir / data["photo"]
            if source.exists():
                with source.open("rb") as fh:
                    person.photo.save(data["photo"], File(fh), save=False)
            else:
                missing.append(data["photo"])
            person.save()

            for j, text in enumerate(data["lines"]):
                PersonLine.objects.create(person=person, text=text, order=j)
            for j, (platform, url) in enumerate(data["social"]):
                PersonSocial.objects.create(person=person, platform=platform, url=url, order=j)

        TeamContent.load()
        self.stdout.write(f"  people          : {len(PEOPLE)} created")
        if missing:
            self.stdout.write(
                self.style.WARNING(f"                    photos not found: {', '.join(missing)}")
            )

    def _seed_testimonials(self, force, media_dir):
        if Testimonial.objects.exists() and not force:
            self.stdout.write(
                f"  testimonials    : {Testimonial.objects.count()} already present, left alone"
            )
            return
        _clear(Testimonial.objects.all(), "photo")

        missing = []
        for i, data in enumerate(TESTIMONIALS):
            row = Testimonial(
                quote=data["quote"], name=data["name"], role=data["role"], order=i
            )
            source = media_dir / data["photo"]
            if source.exists():
                with source.open("rb") as fh:
                    row.photo.save(data["photo"], File(fh), save=False)
            else:
                missing.append(data["photo"])
            row.save()

        longest = max(len(t["quote"]) for t in TESTIMONIALS)
        self.stdout.write(
            f"  testimonials    : {len(TESTIMONIALS)} created "
            f"(longest quote {longest}/{Testimonial.LIMIT} characters)"
        )
        if missing:
            self.stdout.write(
                self.style.WARNING(f"                    photos not found: {', '.join(missing)}")
            )

    def _seed_clients(self, force, media_dir):
        if Client.objects.exists() and not force:
            self.stdout.write(
                f"  clients         : {Client.objects.count()} already present, left alone"
            )
            return
        _clear(Client.objects.all(), "logo")

        missing = []
        for i, data in enumerate(CLIENTS):
            row = Client(name=data["name"], sector=data["sector"], url=data["url"], order=i)
            source = media_dir / data["logo"]
            if source.exists():
                with source.open("rb") as fh:
                    row.logo.save(data["logo"], File(fh), save=False)
            else:
                missing.append(data["logo"])
            row.save()

        ClientsContent.load()
        self.stdout.write(f"  clients         : {len(CLIENTS)} created")
        if missing:
            self.stdout.write(
                self.style.WARNING(f"                    logos not found: {', '.join(missing)}")
            )

    def _seed_footer(self, force):
        FooterContent.load()
        if SocialLink.objects.exists() and not force:
            self.stdout.write(
                f"  social links    : {SocialLink.objects.count()} already present, left alone"
            )
            return
        SocialLink.objects.all().delete()
        for i, (platform, url) in enumerate(SOCIAL):
            SocialLink.objects.create(platform=platform, url=url, order=i)
        self.stdout.write(f"  social links    : {len(SOCIAL)} created")
