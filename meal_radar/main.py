# Importē bibliotēkas
import os       # Darbam ar operētājsistēmu
import json     # JSON apstrādei
import sqlite3  # SQL datubāzēm
import bcrypt   # Paroļu šifrēšanai
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)

# Sesijas konfigurācija
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback_default_key')  # Atslēga sesiju drošībai
app.config['SESSION_COOKIE_NAME'] = 'session'   # Sesijas sīkfailu nosaukums
app.config['SESSION_PERMANENT'] = False         # Sesija netiks saglabāta pēc pārlūka aizvēršanas

# Ceļi (paths) uz SQLite datubāzēm
db_path = os.path.join(os.path.dirname(__file__), 'csv_database.db')    # Pamata datubāze
user_db_path = os.path.join(os.path.dirname(__file__), 'users.db')      # Lietotāju datubžae


# Funkcija (dekorators), lai aizsargātu maršrutus
def login_required(f):
    """
    Pieprasa lietotāja autentifikāciju
    """
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:            # Pārbauda, vai lietotājs ir ielogojies
            return redirect(url_for('login'))   # Ja nav, novirza uz pieteikšanās (login) lapu
        return f(*args, **kwargs)               # Ja ir, izpilda sākotnējo funkciju
    wrapper.__name__ = f.__name__               # Saglabā sākotnējo funkcijas nosaukumu
    return wrapper


# Galvenās lapas maršruts
@app.route('/')
@login_required # Aizsargāts maršruts, tikai pieteikušiem lietotājiem
def home():
    """
    Sistēmas galvenā lapa ar formu produktu meklēšanai.
    """
    return render_template('main.html', inputs=[""] * 10, results=None, error=None)


# Ēdienu meklēšanas maršruts, tiek izsaukts ar pogu "Find Meals"
@app.route('/find_meals', methods=['POST'])
@login_required # Aizsargāts maršruts, tikai pieteikušiem lietotājiem
def find_meals():
    """
    Apstrādā lietotāja ievadi un meklē atbilstošus ēdienus datubāzē.
    """
    # Nolasa lietotāja ievadītos ēdienus meklēšanas formā un attīra no liekām atstarpēm
    food_names = [request.form.get(f'food{i}', '').strip() for i in range(1, 11)]
    food_names = [food for food in food_names if food]  # Atfiltrē tukšos laukus
    # Piešķit sākuma vērtības uzturvērtībām (tās, kuras tiks aprēķinātas un attēlotas uzturvērtību sadaļā)
    initial_percentages = {
        'ENERC': 0,
        'SUGAR': 0,
        'FAT': 0,
        'FASAT': 0,
        'NACL': 0
    }
    initial_nutrient_totals = {
        'ENERC': 0,
        'SUGAR': 0,
        'FAT': 0,
        'FASAT': 0,
        'NACL': 0
    }

    # Pārbauda, vai meklētājā ir ievadīts vismaz viens produkts
    # Ja nav, atgriež kļūdu ar norādi, lai ievada
    if not food_names:
        return render_template(
            'main.html',
            inputs=food_names + [""] * (10 - len(food_names)),
            results=None,
            error="Please enter at least one food name.",
            amounts=[],
            percentages=initial_percentages,
            nutrient_totals=initial_nutrient_totals
        )

    try:
        # Izveido savienojumu ar SQLite datubāzi
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Sagatavo SQL vaicājumu ēdienu meklēšanai, kuru sastāvā ir ievadītie produkti
        query_parts = [f"foodname LIKE ?" for _ in range(len(food_names))]
        query = f"""
            SELECT foodname, enerc, sugar, fat, fasat, nacl
            FROM MealRadarTable
            WHERE {' OR '.join(query_parts)}
        """
        params = [f"%{food}%" for food in food_names] # Aizstāj parametru vērtības
        cursor.execute(query, params)
        results = cursor.fetchall() # Iegūst rezultātus no datubāzes
        conn.close()

        # Pārbauda, vai tika atrasti rezultāti
        # Ja nav, tad atgriež kļūdu un to paziņo
        if not results:
            return render_template(
                'main.html',
                inputs=food_names + [""] * (10 - len(food_names)),
                results=None,
                error="No results found.",
                amounts=[],
                percentages=initial_percentages,
                nutrient_totals=initial_nutrient_totals
            )

        # Piešķir sākuma vērtības ēdienu daudzumiem - visiem 0
        amounts = [0 for _ in results]
        # print(amounts) # Izdrukāšanas iespēja atkļūdošanas vajadzībām

        # Sagatavo datus saglabāšanai JSON failā
        # Atrastie ēdieni tiek saglabāti JSON failā, lai pēc tam vieglāk veikt aprēķinus ar ievadītiem daudzumiem
        data_to_save = {
            'searched_foods': food_names,  # Save the food names the user searched for
            'meal_data': [
                {
                    'foodname': result[0],
                    'enerc': result[1],
                    'sugar': result[2],
                    'fat': result[3],
                    'fasat': result[4],
                    'nacl': result[5],
                    'amount': amounts[i]  # Sākumā 0
                }
                for i, result in enumerate(results)
            ]
        }

        # Saglabā datus JSON failā
        json_file_path = 'meal_data.json'
        with open(json_file_path, 'w') as json_file:
            json.dump(data_to_save, json_file)

        # Formatē rezultātus attēlošanai
        # Nepieciešams nomainīt komatus uz punktiem, lai varētu lietot kā skaitli
        results = [
            (
                item['foodname'],
                item.get('enerc', '0').replace(',', '.'),
                item.get('sugar', '0').replace(',', '.'),
                item.get('fat', '0').replace(',', '.'),
                item.get('fasat', '0').replace(',', '.'),
                item.get('nacl', '0').replace(',', '.')
            )
            for item in data_to_save['meal_data']
        ]

        # Atgriež apstrādātos datus HTML lapai
        return render_template(
            'main.html',
            inputs=food_names + [""] * (10 - len(food_names)),
            results=results,
            error=None,
            amounts=amounts,  # Iedod sākotnējos daudzumus
            percentages=initial_percentages,
            nutrient_totals=initial_nutrient_totals
        )
    except sqlite3.Error as e:
        return render_template(
            'main.html',
            inputs=food_names + [""] * (10 - len(food_names)),
            results=None,
            error=f"Database error: {e}",
            amounts=[],
            percentages=initial_percentages,
            nutrient_totals=initial_nutrient_totals
        )


# Ēdienu uzturvērtību aprēķināšanas maršruts, tiek izsaukts ar pogu "Calculate Nutrient Intake"
@app.route('/calculate_nutrients', methods=['POST'])
@login_required # Aizsargāts maršruts, tikai pieteikušiem lietotājiem
def calculate_nutrients():
    """
    Veic uzturvērtību aprēķinu atbilstoši ievadītiesm ēdienu daudzumiem.
    """
    try:
        # Ielādē ēdienu datus un daudzumus no JSON faila
        json_file_path = 'meal_data.json'
        # Pārbauda, vai JSON fails satur datus
        if not os.path.exists(json_file_path):
            return render_template(
                'main.html',
                inputs=[""] * 10,
                results=None,
                error="No meal data found.",
                amounts=[],
                percentages=None,
                nutrient_totals=None
            )
        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)
            meal_data = data.get('meal_data', [])
            searched_foods = data.get('searched_foods', [])

        # Nolasa lietotāja ievadītos ēdienu daudzumus, un saglabā kā sarakstu
        amounts = list(map(lambda x: int(float(x)), request.form.getlist('amount')))

        
        # Atjauno lauku `amount` json failā
        for i, item in enumerate(meal_data):
            if i < len(amounts):
                item['amount'] = amounts[i]  # Atjauno ēdienu daudzumu vērtības
        
        # Saglabā atjaunotos ēdienu datus atpakaļ JSON failā
        with open(json_file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        # References vērtība diennankts devai
        daily_intake = {
            'ENERC': 8400,  # Enerģija (kJ)
            'SUGAR': 90,    # Cukurs (g)
            'FAT': 70,      # Tauki (g)
            'FASAT': 20,    # Piesātinātās taukskābes (g)
            'NACL': 6000    # Sāls (mg)
        }

        # Aprēķina uzturvērtību kopējās vērtības
        # (saskaita un izdala ar 100, jo references ir uz 100 g)
        nutrient_totals = {
            'ENERC': sum(
                float(item.get('enerc', '0').replace(',', '.')) * amounts[i] / 100 
                for i, item in enumerate(meal_data) 
                if i < len(amounts)
            ),
            'SUGAR': sum(
                float(item.get('sugar', '0').replace(',', '.')) * amounts[i] / 100 
                for i, item in enumerate(meal_data) 
                if i < len(amounts)
            ),
            'FAT': sum(
                float(item.get('fat', '0').replace(',', '.')) * amounts[i] / 100 
                for i, item in enumerate(meal_data) 
                if i < len(amounts)
            ),
            'FASAT': sum(
                float(item.get('fasat', '0').replace(',', '.')) * amounts[i] / 100 
                for i, item in enumerate(meal_data) 
                if i < len(amounts)
            ),
            'NACL': sum(
                float(item.get('nacl', '0').replace(',', '.')) * amounts[i] / 100 
                for i, item in enumerate(meal_data) 
                if i < len(amounts)
            ),
        }

        # Aprēķina uzturvērtību procentuālās vērtības
        percentages = {
            key: (nutrient_totals[key] / daily_intake[key]) * 100
            for key in daily_intake
        }

        # Sagatavo rezultātus, lai parādītu lietotājam
        results = [
            (
                item['foodname'], 
                item.get('enerc', '0').replace(',', '.'), 
                item.get('sugar', '0').replace(',', '.'), 
                item.get('fat', '0').replace(',', '.'), 
                item.get('fasat', '0').replace(',', '.'), 
                item.get('nacl', '0').replace(',', '.')
            )
            for item in meal_data
        ]

        # Nosūta uz saskarni atjaunotos datus
        return render_template(
            'main.html',
            inputs=searched_foods + [""] * (10 - len(searched_foods)),
            results=results,
            error=None,
            amounts=amounts,
            percentages=percentages,
            nutrient_totals=nutrient_totals
        )
    # Kļūdas paziņojums, ja nav bijis iespējams veikt aprēķinu
    except Exception as e:
        return render_template(
            'main.html',
            inputs=[""] * 10,
            results=None,
            error=f"Error calculating nutrients: {e}",
            amounts=[],
            percentages=None,
            nutrient_totals=None
        )


# Ielogošanās maršruts, tiek izsaukts ar pogu "Login"
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Apstrādā lietotāja pieslēgšanos.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(user_db_path) # Savienojums ar lietotāju datubāzi
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        # Pārbauda, vai lietotājs eksistē un parole ir pareiza
        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            session['user_id'] = user[0] # Saglabā lietotāja ID sesijā
            session.modified = True
            return redirect(url_for('home'))
        return render_template('login.html', error="Invalid username or password.")
    
    return render_template('login.html', error=None)


# Reģistrēšanās maršruts, tiek izsaukts ar pogu "Register"
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Apstrādā jaunu lietotāju reģistrāciju.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            # Saglabā jauno lietotāju datubāzē
            conn = sqlite3.connect(user_db_path)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password.decode('utf-8')))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Username already exists.")
    return render_template('register.html', error=None)


@app.route('/about')
def about():
    """
    Atver sadaļu "About Us"
    """
    return render_template('about.html')


@app.route('/logout')
def logout():
    """
    Izraksta lietotāju no sesijas.
    """
    session.pop('user_id', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=False) # Palaiž programmu
