from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.db import get_db

bp = Blueprint('blog', __name__)

LOCATIONS = ["", "Alumni House", "Andersen Auditorium", "Anna Head Alumnae Hall", "Anthony Hall", "Anthropology and Art Practice building", "Archaeological Research Facility", "Bancroft Dance Studio (2401 Bancroft Way)", "Bancroft Library", "Bancroft Parking Structure", "Banway Building (2111 Bancroft Way)", "Barker Hall", "Bauer Wurster Hall", "Bechtel Engineering Center", "Berkeley Art Museum and Pacific Film Archive", "Berkeley Way West", "Birge Hall", "Blackwell Hall", "Blum Hall", "Bowles Hall", "California Hall", "California Memorial Stadium", "Calvin Laboratory", "Campanile (Sather Tower)", "Campbell Hall", "Campus Shared Services", "Career Center", "Cesar E. Chavez Student Center", "Channing-Bowditch Apartments", "Cheit Hall", "Chou Hall", "CITRIS", "Clark Kerr Campus", "Cleary Hall", "CNMAT (1750 Arch St)", "Cory Hall", "Davis Hall", "Doe Memorial Library", "Donner Laboratory", "Durant Hall", "Durham Studio Theater", "Dwight Way Child Development Center", "Dwinelle Annex", "Dwinelle Hall", "Earthquake Engineering Library", "East Asian Library", "East Asian Studies, Institute of", "Ellsworth Parking Structure", "Eshleman Hall", "Etcheverry Hall", "Evans Hall", "Extension", "Faculty Club", "Foothill Residence Halls", "Fox Cottage (2350 Bowditch)", "Genetics and Plant Biology", "Giannini Hall", "Giauque Hall", "Gilman Hall", "Golden Bear Center (1995 University Ave)", "Goldman School", "Graduate Theological Union", "Greek Theatre", "Haas Clubhouse", "Haas Pavilion", "Haas School of Business", "Hargrove Music Library", "Haste Street Child Development Center", "Haviland Hall", "Hearst Field Annex", "Hearst Greek Theatre", "Hearst Memorial Gymnasium", "Hearst Memorial Mining Building", "Hellman Tennis Center", "Henry H. Wheeler Brain Imaging Center", "Hertz Hall", "Hesse Hall", "Hildebrand Hall", "Hilgard Hall", "Ida Louise Jackson Graduate House", "Innovative Genomics Institute Building", "Insectary Greenhouse", "International House", "Investigative Reporting Program", "Jackson Graduate House",
             "Jacobs Hall", "Jones Child Study Center", "Julia Morgan Hall", "Koret Visitor Center", "Koshland Hall", "Latimer Hall", "Latin American Studies, Center for", "Law Building", "Lawrence Berkeley National Laboratory", "Lawrence Hall of Science", "Legends Aquatic Center", "Lewis Hall", "Li Ka Shing Center", "Library", "Lower Hearst Parking Structure", "Magnes Collection of Jewish Art and Life", "Manville Hall", "Martin Luther King, Jr. Student Union", "Martinez Commons", "Mathematical Sciences Research Institute (MSRI)", "Maxwell Family Field and Stadium Garage", "McCone Hall", "McLaughlin Hall", "Melvin Calvin Laboratory", "Minor Hall", "Minor Hall Addition", "Moffitt Library", "Morgan Hall", "Morrison Hall", "Moses Hall", "Mulford Hall", "Murphy Hall", "Natural Resources Laboratory", "North Gate Hall", "Northern Regional Library Facility", "O'Brien Hall", "Office of Public Affairs", "Old Art Gallery", "Oxford Research Unit", "Pacific Film Archive, Berkeley Art Museum and", "Parking and Transportation", "Physics North and South", "Pimentel Hall", "Public Affairs, Office of", "Recreational Sports Facility", "Residential & Student Services Building", "Sather Tower", "Senior Hall", "Simon Hall", "Simpson Center for Student-Athlete High Performance", "Social Sciences Building", "Soda Hall", "South Hall", "Southeast Asian Studies, Center for", "Space Sciences Laboratory", "Spieker Aquatics Complex", "Sproul Hall", "Stanley Hall", "Starr East Asian Library", "Stephens Hall", "Stern Hall", "Student Union", "Summer Session", "Sutardja Dai Hall", "Tan Hall", "Tang Center", "The Law Building", "UC Berkeley Extension", "Underhill Parking Facility & Playing Field", "Unit 1 Resident Hall", "Unit 2 Resident Hall", "Unit 3 Resident Hall", "University Hall", "University Health Services", "University House", "Upper Hearst Parking Structure", "Valley Life Sciences Building", "Visitor Center", "Warren Hall", "Weill Hall", "Wellman Hall", "Wheeler Hall", "Women's Faculty Club", "Woo Hon Fai Hall", "Zellerbach Hall"]


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        print('creating post')
        start_address = request.form['start_location']
        end_address = request.form['end_location']
        time = request.form['date'] + ' ' + request.form['time'] + ':00'
        error = None

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO rides (start_address, end_address, time, author_id)'
                ' VALUES (?, ?, ?, ?)',
                (start_address, end_address, time, g.accounts['id'])
            )
            db.commit()
            return redirect(url_for('blog.schedule'))

    return render_template('blog/create.html', locations=LOCATIONS)


@bp.route('/', methods=('GET',))
def index():
    return redirect(url_for('blog.schedule'))


@bp.route('/schedule', methods=('GET',))
@login_required
def schedule():
    if g.accounts['role'] == 'staff':
        rides = get_db().execute(
            'SELECT start_address, end_address, time, driver, r.id, username FROM rides '
            'r JOIN accounts a ON a.id = r.author_id'
        ).fetchall()
    else:
        rides = get_db().execute(
            'SELECT start_address, end_address, time, driver, id FROM rides WHERE author_id = ?', (
                g.accounts['id'],)
        ).fetchall()

    return render_template('blog/index.html', rides=rides)


@bp.route('/dashboard', methods=('GET',))
@login_required
def dashboard():
    print('showing dashboard')

    db = get_db()
    name = get_db().execute(
        'SELECT username FROM accounts WHERE id = ?', (g.accounts['id'],)
    ).fetchone()
    print(name['username'])

    total_rides = get_db().execute(
        'SELECT COUNT(*) FROM rides WHERE author_id = ?', (g.accounts['id'],)
    ).fetchone()
    print(total_rides['COUNT(*)'])

    return 'This is the dashboard.'


def get_ride(id, check_staff=True):
    ride = get_db().execute(
        'SELECT start_address, end_address, time, username, driver, author_id'
        ' FROM rides r JOIN accounts a ON a.id = r.author_id'
        ' WHERE r.id = ?',
        (id,)
    ).fetchone()
    print(dict(ride))

    if ride is None:
        abort(404, "Ride id {0} doesn't exist.".format(id))

    if g.accounts['role'] != 'staff' and (g.accounts['id'] != ride['author_id']):
        abort(403, "Not authorized to access ride")

    return ride


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    ride = get_ride(id)

    if request.method == 'POST':
        start_address = request.form['start_location']
        end_address = request.form['end_location']
        time = request.form['date'] + ' ' + request.form['time'] + ':00'
        driver = request.form['driver'] or None
        error = None

        if not ride:
            error = 'Ride is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE rides SET start_address = ?, end_address = ?, time = ?, '
                'driver = ? WHERE id = ?',
                (start_address, end_address, time, driver, id)
            )
            db.commit()
            return redirect(url_for('blog.schedule'))

    return render_template('blog/update.html', ride=ride, locations=LOCATIONS)
