from flask import Flask, render_template, request, redirect
import pandas as pd
import plotly.express as px
from bs4 import BeautifulSoup
from joblib import load
from sklearn.preprocessing import LabelEncoder
import sqlite3


app = Flask(__name__)

# Function to create the database table
def create_table():
    conn = sqlite3.connect('police_details.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS police_details (
                 username TEXT,
                 police_gmail TEXT,
                 name TEXT,
                 position TEXT,
                 password TEXT)''')
    conn.commit()
    conn.close()

# Function to insert data into the database
def insert_data(username, police_gmail, name, position, password):
    conn = sqlite3.connect('police_details.db')
    c = conn.cursor()
    c.execute("INSERT INTO police_details (username, police_gmail, name, position, password) VALUES (?, ?, ?, ?, ?)",
              (username, police_gmail, name, position, password))
    conn.commit()
    conn.close()

# Function to check user credentials
def check_credentials(username, password):
    conn = sqlite3.connect('police_details.db')
    c = conn.cursor()
    c.execute("SELECT * FROM police_details WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()
    return result is not None

# Route for the login form submission
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if check_credentials(username, password):
        return redirect('/home')
    else:
        return "Wrong username or password. Please try again."

# Route for the sign up form submission
@app.route('/signup', methods=['POST'])
def signup():
    police_gmail = request.form['username']
    username = request.form['email']
    name = request.form['firstName']
    position = request.form['lastName']
    password = request.form['password']
    insert_data(police_gmail, username, name, position, password)
    return redirect('/home')

# Function to render the index.html page
@app.route('/')
def index():
    create_table()
    return render_template('index.html')

@app.route('/home')
def home():
    # Route to the sign-up/login page
    return render_template('home.html')

# Load the trained model
model = load('model.joblib')

# Load the label encoder for district names
label_encoder = load('label_encoder.joblib')  # Assuming you saved label_encoder during training

# Define district names for dropdown menu
district_names = ['Bagalkot', 'Yadgir','Bengaluru City','Tumakuru','Bengaluru Dist','Hassan','Mandya','Belagavi Dist','Chitradurga','Shivamogga','Mysuru Dist','Ramanagara','Udupi','Uttara Kannada','Bidar','Mangaluru City','Davanagere','Vijayapur','Chikkamagaluru','Dakshina Kannada','Mysuru City','Haveri','Kalaburagi','Chickballapura','Raichur','Kolar','Belagavi City','Koppal','Chamarajanagar','Ballari','Vijayanagara','Dharwad','Kodagu','Kalaburagi City','K.G.F','Karnataka Railways','Gadag','Hubballi Dharwad City']  # Add more districts as needed

@app.route('/map')
def map():
    return render_template('map.html', district_names=district_names)

@app.route('/map', methods=['POST'])
def predict():
    if request.method == 'POST':
        district_name = request.form['district_name']
        year = int(request.form['year'])

        # Encode district name to numerical value using label encoder
        district_id = label_encoder.transform([district_name])[0]

        # Predict accidents for the input district and year
        predicted_accidents = int(model.predict([[district_id, year]]))

        return render_template('map.html', district_names=district_names, selected_district=district_name,
                               year=year, predicted_accidents=predicted_accidents)

@app.route('/record_entry')
def record_entry():
    return render_template('record_entry.html')

def create_table2():
    conn = sqlite3.connect('police_details.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS feedback_details (
                 feedback TEXT)''')
    conn.commit()
    conn.close()

# Function to insert data into the database
def insert_data2(feedback):
    conn = sqlite3.connect('police_details.db')
    c = conn.cursor()
    c.execute("INSERT INTO feedback_details (feedback) VALUES (?)",
              (feedback,))
    conn.commit()
    conn.close()

@app.route('/feedback', methods=['POST'])
def feedback():
    feedback = request.form['feedback']
    create_table2()
    insert_data2(feedback)
    return redirect('/home')

@app.route('/home')
def index2():
    create_table()
    return render_template('home.html')


@app.route('/accident_recordentry')
def accident_recordentry():
    return render_template('accident_recordentry.html')


@app.route('/static/css/css_styles')
def serve_css(css_styles):
    return app.send_static_file(f'css/{css_styles}')

# accident probablity
def get_road_details(road_name):
    # Path to the HTML file containing road construction/renovation details
    file_path = 'road_data.html'
    
    # Read the HTML file
    with open(file_path, 'r') as file:
        html_content = file.read()
    
    # Parse HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find details specific to the entered road name
    # Search for road names that contain the entered input partially
    road_details = None
    for div in soup.find_all('div', class_='road-details'):
        road_data = div['data-road']
        if road_name.lower() in road_data.lower():
            road_details = div.get_text()
            break
    
    if road_details:
        return road_details
    else:
        return "No construction or renovation planned at the moment."
    
@app.route('/prediction')
def prediction():
    return render_template('prediction.html')

@app.route('/accident_probablity', methods=['GET', 'POST'])
def accident_probablity():
    if request.method == 'POST':
        road_name = request.form['road_name']
        road_details = get_road_details(road_name)
        return render_template('accident_probablity.html', road_details=road_details, road_name=road_name)
    else:
        return render_template('accident_probablity.html', road_details=None, road_name=None)




@app.route('/accident_analysis', methods=['GET', 'POST'])
def accident_analysis():
    csv_file = 'accident_data.csv'  # Filename of your CSV file

    # Read CSV file
    data = pd.read_csv(csv_file)

    # Get unique values for each column
    options_column1 = data['DISTRICTNAME'].unique().tolist()
    options_column2 = data['Weather'].unique().tolist()
    options_column3 = data['Severity'].unique().tolist()
    options_column4 = data['Year'].unique().tolist()
    options_column5 = data['UNITNAME'].unique().tolist()
    options_column6 = data['Accident_Location'].unique().tolist()
    options_column7 = data['Accident_SubLocation'].unique().tolist()
    options_column8 = data['Hit_Run'].unique().tolist()

    filtered_data = None  # Initialize filtered data variable

    if request.method == 'POST':
        column1_value = request.form.get('element_name1')  # Get selected value for column 1
        column2_value = request.form.get('element_name2')  # Get selected value for column 2
        column3_value = request.form.get('element_name3')  # Get selected value for column 3
        column4_value = request.form.get('element_name4')  # Get selected value for column 4
        column5_value = request.form.get('element_name5')  # Get selected value for column 5
        column6_value = request.form.get('element_name6')  # Get selected value for column 6
        column7_value = request.form.get('element_name7')  # Get selected value for column 7
        column8_value = request.form.get('element_name8')  # Get selected value for column 8


        # Apply filters based on selected values, even if they are empty
        filtered_data = data
        if column1_value:
            filtered_data = filtered_data[filtered_data['DISTRICTNAME'] == column1_value]
        if column2_value:
            filtered_data = filtered_data[filtered_data['Weather'] == column2_value]
        if column3_value:
            filtered_data = filtered_data[filtered_data['Severity'] == column3_value]
        if column4_value:
            filtered_data = filtered_data[filtered_data['Year'] == int(column4_value)]  # Convert to int for comparison
        if column5_value:
            filtered_data = filtered_data[filtered_data['UNITNAME'] == column5_value] 
        if column6_value:
            filtered_data = filtered_data[filtered_data['Accident_Location'] == column6_value] 
        if column7_value:
            filtered_data = filtered_data[filtered_data['Accident_SubLocation'] == column7_value]
        if column8_value:
            filtered_data = filtered_data[filtered_data['Hit_Run'] == column8_value] 

    return render_template('accident_analysis.html', options_column1=options_column1,
                           options_column2=options_column2, options_column3=options_column3,
                           options_column4=options_column4, options_column5=options_column5,
                           options_column6=options_column6, options_column7=options_column7,
                           options_column8=options_column8,
                           filtered_data=filtered_data)


@app.route('/accident_dashboard', methods=['GET', 'POST'])
def accident_dashboard():
    csv_file = 'accident_data.csv'  # Filename of your CSV file

    # Read CSV file
    data = pd.read_csv(csv_file)

    # Get unique values for each column
    options_column1 = data['DISTRICTNAME'].unique().tolist()
    options_column2 = data['Weather'].unique().tolist()
    options_column3 = data['Severity'].unique().tolist()
    options_column4 = data['Year'].unique().tolist()
    options_column5 = data['Road_Type'].unique().tolist()
    options_column6 = data['Accident_Location'].unique().tolist()
    options_column7 = data['Accident_SubLocation'].unique().tolist()
    options_column8 = data['Hit_Run'].unique().tolist()

    filtered_data = None  # Initialize filtered data variable
    total_filtered_rows = 0  # Initialize total filtered rows variable
    max_occurrence_sublocation = None
    max_occurrence_count = None
    severity_graph_html = None
    year_pie_chart_html = None
    Road_Type_graph_html = None
    no_of_vehicles_involved_count = None

    if request.method == 'POST':
        column1_value = request.form.get('element_name1')  # Get selected value for column 1
        column2_value = request.form.get('element_name2')  # Get selected value for column 2
        column3_value = request.form.get('element_name3')  # Get selected value for column 3
        column4_value = request.form.get('element_name4')  # Get selected value for column 4
        column5_value = request.form.get('element_name5')  # Get selected value for column 5
        column6_value = request.form.get('element_name6')  # Get selected value for column 6
        column7_value = request.form.get('element_name7')  # Get selected value for column 7
        column8_value = request.form.get('element_name8')  # Get selected value for column 8

        # Apply filters based on selected values, even if they are empty
        filtered_data = data
        if column1_value:
            filtered_data = filtered_data[filtered_data['DISTRICTNAME'] == column1_value]
        if column2_value:
            filtered_data = filtered_data[filtered_data['Weather'] == column2_value]
        if column3_value:
            filtered_data = filtered_data[filtered_data['Severity'] == column3_value]
        if column4_value:
            filtered_data = filtered_data[filtered_data['Year'] == int(column4_value)]  # Convert to int for comparison
        if column5_value:
            filtered_data = filtered_data[filtered_data['Road_Type'] == column5_value]
        if column6_value:
            filtered_data = filtered_data[filtered_data['Accident_Location'] == column6_value]
        if column7_value:
            filtered_data = filtered_data[filtered_data['Accident_SubLocation'] == column7_value]
        if column8_value:
            filtered_data = filtered_data[filtered_data['Hit_Run'] == column8_value]

        # Count occurrences of each unique element in the 'Severity' column
        severity_counts = filtered_data['Severity'].value_counts()

        # Create Plotly bar chart for severity distribution
        fig_severity = px.bar(x=severity_counts.index, y=severity_counts.values,
                              labels={'x':'Severity', 'y':'Count'}, title='Severity Distribution')

        # Convert Plotly figure to HTML
        severity_graph_html = fig_severity.to_html(full_html=False)

        # Count occurrences of each unique element in the 'Year' column
        year_counts = filtered_data['Year'].value_counts()

        # Create Plotly pie chart for year distribution
        fig_year = px.pie(values=year_counts.values, names=year_counts.index, title='Year Distribution')

        # Convert Plotly figure to HTML
        year_pie_chart_html = fig_year.to_html(full_html=False)

        # Count occurrences of each unique element in the 'road type' column
        Road_Type_counts = filtered_data['Road_Type'].value_counts()

        # Create Plotly bar chart for Road_Type distribution
        fig_Road_Type = px.bar(x=Road_Type_counts.index, y=Road_Type_counts.values,
                              labels={'x':'Road_Type', 'y':'Count'}, title='Road Type Distribution')

        # Convert Plotly figure to HTML
        Road_Type_graph_html = fig_Road_Type.to_html(full_html=False)

        # Count the total number of filtered rows
        total_filtered_rows = len(filtered_data)

        # Count occurrences of each unique element in the 'Accident_SubLocation' column
        sublocation_counts = filtered_data['Accident_SubLocation'].value_counts()

        # Get the index of the maximum count
        max_index = sublocation_counts.idxmax()

        # Store the name of the element with the maximum occurrence
        max_occurrence_sublocation = max_index if max_index else "No data"  # Provide a default value if there's no data

         # Get the maximum occurrence count
        max_occurrence_count = sublocation_counts.max()

        # Count occurrences of the specified value (1) in the 'Noofvehicle_involved' column
        no_of_vehicles_involved_count = filtered_data['Noofvehicle_involved'].apply(lambda x: 1 if x == 1 else 0).sum()
        no_of_vehicles_involved_count = int(no_of_vehicles_involved_count / 2)


    return render_template('accident_dashboard.html', options_column1=options_column1,
                           options_column2=options_column2, options_column3=options_column3,
                           options_column4=options_column4, options_column5=options_column5,
                           options_column6=options_column6, options_column7=options_column7,
                           options_column8=options_column8,
                           filtered_data=filtered_data, severity_graph_html=severity_graph_html,
                           year_pie_chart_html=year_pie_chart_html, Road_Type_graph_html=Road_Type_graph_html,
                           total_filtered_rows=total_filtered_rows,  max_occurrence_sublocation=max_occurrence_sublocation,
                           max_occurrence_count=max_occurrence_count,
                           no_of_vehicles_involved_count=no_of_vehicles_involved_count)



@app.route('/accused_dashboard', methods=['GET', 'POST'])
def accused_dashboard():
    csv_file = 'accused_data.csv'  # Filename of your CSV file

    # Read CSV file
    data = pd.read_csv(csv_file)

    # Get unique values for each column
    options_column1 = data['District_Name'].unique().tolist()
    options_column2 = data['Sex'].unique().tolist()
    options_column3 = data['age'].unique().tolist()
    options_column4 = data['Year'].unique().tolist()
    options_column5 = data['Profession'].unique().tolist()
    options_column6 = data['Month'].unique().tolist()
    options_column7 = data['Caste'].unique().tolist()
    options_column8 = data['UnitName'].unique().tolist()

    filtered_data = None  # Initialize filtered data variable
    total_filtered_rows = 0  # Initialize total filtered rows variable
    max_occurrence_sublocation = None
    max_occurrence_count = None
    age_graph_html = None
    year_pie_chart_html = None
    Road_Type_graph_html = None

    if request.method == 'POST':
        column1_value = request.form.get('element_name1')  # Get selected value for column 1
        column2_value = request.form.get('element_name2')  # Get selected value for column 2
        column3_value = request.form.get('element_name3')  # Get selected value for column 3
        column4_value = request.form.get('element_name4')  # Get selected value for column 4
        column5_value = request.form.get('element_name5')  # Get selected value for column 5
        column6_value = request.form.get('element_name6')  # Get selected value for column 6
        column7_value = request.form.get('element_name7')  # Get selected value for column 7
        column8_value = request.form.get('element_name8')  # Get selected value for column 8

        # Apply filters based on selected values, even if they are empty
        filtered_data = data
        if column1_value:
            filtered_data = filtered_data[filtered_data['District_Name'] == column1_value]
        if column2_value:
            filtered_data = filtered_data[filtered_data['Sex'] == column2_value]
        if column3_value:
            filtered_data = filtered_data[filtered_data['age'] == column3_value]
        if column4_value:
            filtered_data = filtered_data[filtered_data['Year'] == int(column4_value)]  # Convert to int for comparison
        if column5_value:
            filtered_data = filtered_data[filtered_data['Profession'] == column5_value]
        if column6_value:
            filtered_data = filtered_data[filtered_data['Month'] == column6_value]
        if column7_value:
            filtered_data = filtered_data[filtered_data['Caste'] == column7_value]
        if column8_value:
            filtered_data = filtered_data[filtered_data['UnitName'] == column8_value]


        # Count occurrences of each unique element in the 'Year' column
        year_counts = filtered_data['Year'].value_counts()

        # Create Plotly pie chart for year distribution
        fig_year = px.pie(values=year_counts.values, names=year_counts.index, title='Year Distribution')

        # Convert Plotly figure to HTML
        year_pie_chart_html = fig_year.to_html(full_html=False)

        # Count occurrences of each unique element in the 'road type' column
        Road_Type_counts = filtered_data['Sex'].value_counts()

        # Create Plotly bar chart for Road_Type distribution
        fig_Road_Type = px.bar(x=Road_Type_counts.index, y=Road_Type_counts.values,
                              labels={'x':'Sex', 'y':'Count'}, title='Sex Distribution')

        # Convert Plotly figure to HTML
        Road_Type_graph_html = fig_Road_Type.to_html(full_html=False)

        # Count the total number of filtered rows
        total_filtered_rows = len(filtered_data)

        # Count occurrences of each unique element in the 'Accident_SubLocation' column
        sublocation_counts = filtered_data['Sex'].value_counts()

        # Get the index of the maximum count
        max_index = sublocation_counts.idxmax()

        # Store the name of the element with the maximum occurrence
        max_occurrence_sublocation = max_index if max_index else "No data"  # Provide a default value if there's no data

         # Get the maximum occurrence count
        max_occurrence_count = sublocation_counts.max()

        # Convert 'age' column to integer type
        filtered_data['age'] = filtered_data['age'].astype(int)
        
        # Group ages into bins (e.g., 0-20, 21-40, 41-60, etc.)
        age_bins = pd.cut(filtered_data['age'], bins=[0, 20, 40, 60, 80, 100])
        
        # Count occurrences of each age group
        age_group_counts = age_bins.value_counts().sort_index()
        
        # Create Plotly bar chart for age distribution
        fig_age = px.bar(x=age_group_counts.index.astype(str), y=age_group_counts.values,
                        labels={'x': 'Age Group', 'y': 'Count'}, title='Age Distribution')

        # Convert Plotly figure to HTML
        age_graph_html = fig_age.to_html(full_html=False)


    return render_template('accused_dashboard.html', options_column1=options_column1,
                           options_column2=options_column2, options_column3=options_column3,
                           options_column4=options_column4, options_column5=options_column5,
                           options_column6=options_column6, options_column7=options_column7,
                           options_column8=options_column8,
                           filtered_data=filtered_data, age_graph_html=age_graph_html,
                           year_pie_chart_html=year_pie_chart_html, Road_Type_graph_html=Road_Type_graph_html,
                           total_filtered_rows=total_filtered_rows,  max_occurrence_sublocation=max_occurrence_sublocation,max_occurrence_count=max_occurrence_count)

# victime dashboard
@app.route('/victim_dashboard', methods=['GET', 'POST'])
def victim_dashboard():
    csv_file = 'victim_data.csv'  # Filename of your CSV file

    # Read CSV file
    data = pd.read_csv(csv_file)

    # Get unique values for each column
    options_column1 = data['District_Name'].unique().tolist()
    options_column2 = data['Sex'].unique().tolist()
    options_column3 = data['age'].unique().tolist()
    options_column4 = data['Year'].unique().tolist()
    options_column5 = data['InjuryType'].unique().tolist()
    options_column6 = data['Month'].unique().tolist()
    options_column7 = data['Caste'].unique().tolist()
    options_column8 = data['UnitName'].unique().tolist()

    filtered_data = None  # Initialize filtered data variable
    total_filtered_rows = 0  # Initialize total filtered rows variable
    max_occurrence_sublocation = None
    max_occurrence_count = None
    age_graph_html = None
    year_pie_chart_html = None
    Road_Type_graph_html = None

    if request.method == 'POST':
        column1_value = request.form.get('element_name1')  # Get selected value for column 1
        column2_value = request.form.get('element_name2')  # Get selected value for column 2
        column3_value = request.form.get('element_name3')  # Get selected value for column 3
        column4_value = request.form.get('element_name4')  # Get selected value for column 4
        column5_value = request.form.get('element_name5')  # Get selected value for column 5
        column6_value = request.form.get('element_name6')  # Get selected value for column 6
        column7_value = request.form.get('element_name7')  # Get selected value for column 7
        column8_value = request.form.get('element_name8')  # Get selected value for column 8

        # Apply filters based on selected values, even if they are empty
        filtered_data = data
        if column1_value:
            filtered_data = filtered_data[filtered_data['District_Name'] == column1_value]
        if column2_value:
            filtered_data = filtered_data[filtered_data['Sex'] == column2_value]
        if column3_value:
            filtered_data = filtered_data[filtered_data['age'] == column3_value]
        if column4_value:
            filtered_data = filtered_data[filtered_data['Year'] == int(column4_value)]  # Convert to int for comparison
        if column5_value:
            filtered_data = filtered_data[filtered_data['InjuryType'] == column5_value]
        if column6_value:
            filtered_data = filtered_data[filtered_data['Month'] == column6_value]
        if column7_value:
            filtered_data = filtered_data[filtered_data['Caste'] == column7_value]
        if column8_value:
            filtered_data = filtered_data[filtered_data['UnitName'] == column8_value]


        # Count occurrences of each unique element in the 'Year' column
        year_counts = filtered_data['Year'].value_counts()

        # Create Plotly pie chart for year distribution
        fig_year = px.pie(values=year_counts.values, names=year_counts.index, title='Year Distribution')

        # Convert Plotly figure to HTML
        year_pie_chart_html = fig_year.to_html(full_html=False)

        # Count occurrences of each unique element in the 'road type' column
        Road_Type_counts = filtered_data['Sex'].value_counts()

        # Create Plotly bar chart for Road_Type distribution
        fig_Road_Type = px.bar(x=Road_Type_counts.index, y=Road_Type_counts.values,
                              labels={'x':'Sex', 'y':'Count'}, title='Sex Distribution')

        # Convert Plotly figure to HTML
        Road_Type_graph_html = fig_Road_Type.to_html(full_html=False)

        # Count the total number of filtered rows
        total_filtered_rows = len(filtered_data)

        # Count occurrences of each unique element in the 'Accident_SubLocation' column
        sublocation_counts = filtered_data['Sex'].value_counts()

        # Get the index of the maximum count
        max_index = sublocation_counts.idxmax()

        # Store the name of the element with the maximum occurrence
        max_occurrence_sublocation = max_index if max_index else "No data"  # Provide a default value if there's no data

         # Get the maximum occurrence count
        max_occurrence_count = sublocation_counts.max()

        # Convert 'age' column to integer type
        filtered_data['age'] = filtered_data['age'].astype(int)
        
        # Group ages into bins (e.g., 0-20, 21-40, 41-60, etc.)
        age_bins = pd.cut(filtered_data['age'], bins=[0, 20, 40, 60, 80, 100])
        
        # Count occurrences of each age group
        age_group_counts = age_bins.value_counts().sort_index()
        
        # Create Plotly bar chart for age distribution
        fig_age = px.bar(x=age_group_counts.index.astype(str), y=age_group_counts.values,
                        labels={'x': 'Age Group', 'y': 'Count'}, title='Age Distribution')

        # Convert Plotly figure to HTML
        age_graph_html = fig_age.to_html(full_html=False)


    return render_template('victim_dashboard.html', options_column1=options_column1,
                           options_column2=options_column2, options_column3=options_column3,
                           options_column4=options_column4, options_column5=options_column5,
                           options_column6=options_column6, options_column7=options_column7,
                           options_column8=options_column8,
                           filtered_data=filtered_data, age_graph_html=age_graph_html,
                           year_pie_chart_html=year_pie_chart_html, Road_Type_graph_html=Road_Type_graph_html,
                           total_filtered_rows=total_filtered_rows,  max_occurrence_sublocation=max_occurrence_sublocation,max_occurrence_count=max_occurrence_count)


if __name__ == '__main__':
    app.run(debug=True)
