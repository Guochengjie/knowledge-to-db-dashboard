# Knowledge 2 DB Dashboard
Convert knowledge system for intelligent cities into mysql database and Java Spring Boot API

- ✅ `Up-to-date dependencies`
- ✅ `Database`: `SQLite`, MySql
  - Silent fallback to `SQLite`
- ✅ `DB Tools`: SQLAlchemy ORM, `Flask-Migrate`
- ✅ `Authentication`, Session Based, `OAuth` via **Github**
- ✅ `Dark Mode` (persistent)
- ✅ Docker, `Flask-Minify` (page compression)
- 🚀 `Deployment` 
  - `CI/CD` flow via `Render`

## ✨ Quick start in `Docker`

```bash
$ docker-compose up --build 
```

Visit `http://localhost:5085` in your browser. The app should be up & running.

### ✨ Create a new `.env` file using sample `env.sample`

The meaning of each variable can be found below: 

- `DEBUG`: if `True` the app runs in development mode
  - For production value `False` should be used
- `ASSETS_ROOT`: used in assets management
  - default value: `/static/assets`

### ✨ Change the Youdao API key for translation (Optional)
If you want to change to your own Youdao API, you need to create a vocabulary list. 

| Chinese | English                         |
|---------|---------------------------------|
| 基础属性    | base attributes                 |
| 事       | event                           |
| 物       | object                          |
| 组织      | organization                    |
| 地       | region                          |
| 功能      | functionality                   |
| 民族      | ethnicity                       |
| 皮基站     | pico base station               |
| 地_组织    | region_organization             |
| 组织_人    | organization_user               |
| 组织_地    | organization_region             |
| 物_人     | object_user                     |
| 物_组织    | object_organization             |
| 人_地     | user_region                     |
| 人_物     | user_object                     |
| 组织_物    | organization_object             |
| 人_人     | user_user                       |
| 事_物     | event_object                    |
| 物_事     | object_event                    |
| 事_地     | event_region                    |
| 地_物     | region_object                   |
| 人_事     | user_event                      |
| 事_人     | event_user                      |
| 地_地     | region_region                   |
| 地_人     | region_user                     |
| 事_事     | event_event                     |
| 人_组织    | user_organization               |
| 组织_组织   | organization_organization       |
| 事_组织    | event_organization              |
| 组织_事    | organization_event              |
| 物_地     | object_region                   |
| 地_事     | region_event                    |
| 物_物     | object_object                   |
| 人-人     | user_user                       |
| 组织-组织   | organization_organization       |
| 事-物     | event_object                    |
| 事-组织    | event_organization              |
| 事-地     | event_region                    |
| 物-事     | object_event                    |
| 地-物     | region_object                   |
| 组织-人    | organization_user               |
| 地-地     | region_region                   |
| 地-人     | region_user                     |
| 组织-地    | organization_region             |
| 人-事     | user_event                      |
| 事-人     | event_user                      |
| 物-地     | object_region                   |
| 组织-物    | organization_object             |
| 物-物     | object_object                   |
| 地-事     | region_event                    |
| 人-组织    | user_organization               |
| 事-事     | event_event                     |
| 地-组织    | region_organization             |
| 物-组织    | object_organization             |
| 人-地     | user_region                     |
| 物-人     | object_user                     |
| 组织-事    | organization_event              |
| 人-物     | user_object                     |
| 同类关系    | relations of a  same kind       |
| 相互关系    | relations of 2  different kinds |
| 人       | user                            |
| 地点      | region                          |
| 微信开放ID  | wx open id                      |
| 在京      | in Beijing                      |
| 登录状态    | auth flag                       |
| 父地点UUID | parent region id                |
| 区域编码    | region code                     |
| 是否登录    | auth flag                       |
| 地址层级全称  | full address                    |
| 区域编码    | region code                     |
| 父地点UUID | parent region id                |

## ✨ Manual Build


### 👉 Set Up for `Unix`, `MacOS` 

> Install modules via `VENV` or Conda Environment

#### `VENV`

```bash
$ virtualenv env.sample
$ source env.sample/bin/activate
$ pip3 install -r requirements.txt
```

#### `Conda`
Please change the `env.sample` to the name you want

```bash
$ conda create -n env.sample python=3.9
$ conda activate env.sample
$ pip install -r requirements.txt
```

<br />

> Set Up Flask Environment

```bash
$ export FLASK_APP=run.py
$ export FLASK_ENV=development
```

Set up other environment variables in `.env` file.
```bash
$ export DB_ENGINE=mysql+pymysql
$ export DB_HOST=
$ export DB_PORT=
$ export DB_USERNAME=
$ export DB_PASS=
$ export DB_NAME=
```

<br />

> Start the app

```bash
$ flask run
// OR
$ flask run --cert=adhoc # For HTTPS server
```

At this point, the app runs at `http://127.0.0.1:5000/`. 

<br />

### 👉 Create Users

By default, the app redirects guest users to authenticate. In order to access the private pages, follow this set up: 

- Start the app via `flask run`
- Access the `registration` page and create a new user:
  - `http://127.0.0.1:5000/register`
- Access the `sign in` page and authenticate
  - `http://127.0.0.1:5000/login`

<br />

## ✨ Code-base structure

The project is coded using blueprints, app factory pattern, dual configuration profile (development and production) and an intuitive structure presented bellow:

```bash
< PROJECT ROOT >
   |
   |-- apps/
   |    |
   |    |-- home/                           # A simple app that serve HTML files
   |    |    |-- routes.py                  # Define app routes
   |    |    |-- models.py                  # Defines models 
   |    |    |-- forms.py                   # Define app forms
   |    |
   |    |-- authentication/                 # Handles auth routes (login and register)
   |    |    |-- routes.py                  # Define authentication routes  
   |    |    |-- models.py                  # Defines models  
   |    |    |-- forms.py                   # Define auth forms (login and register) 
   |    |
   |    |-- static/
   |    |    |-- <css, JS, images>          # CSS files, Javascripts files
   |    |
   |    |-- templates/                      # Templates used to render pages
   |    |    |-- includes/                  # HTML chunks and components
   |    |    |    |-- navigation.html       # Top menu component
   |    |    |    |-- sidebar.html          # Sidebar component
   |    |    |    |-- footer.html           # App Footer
   |    |    |    |-- scripts.html          # Scripts common to all pages
   |    |    |
   |    |    |-- layouts/                   # Master pages
   |    |    |    |-- base-fullscreen.html  # Used by Authentication pages
   |    |    |    |-- base.html             # Used by common pages
   |    |    |
   |    |    |-- accounts/                  # Authentication pages
   |    |    |    |-- login.html            # Login page
   |    |    |    |-- register.html         # Register page
   |    |    |
   |    |    |-- home/                      # UI Kit Pages
   |    |         |-- index.html            # Index page
   |    |         |-- 404-page.html         # 404 page
   |    |         |-- *.html                # All other pages
   |    |--Uploads/                         # Uploads folder
   |  config.py                             # Set up the app
   |    __init__.py                         # Initialize the app
   |
   |-- requirements.txt                     # App Dependencies
   |
   |-- .env.sample                                 # Inject Configuration via Environment
   |-- run.py                               # Start the app - WSGI gateway
   |
   |-- knowledge2db/                        # Knowledge to Database package
   |-- PackageGenerator/                    # Package Generator package
   |-- ************************************************************************
```

<br />
