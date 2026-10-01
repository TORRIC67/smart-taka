// src/i18n.js - plain JS translation store (no React needed here), so it can be
// imported from anywhere, including non-component files like api/client.js.
// Language choice is kept in localStorage and shared across tabs/reloads.

export const LANGUAGES = { sw: "Kiswahili", en: "English", fr: "Français" };
const STORAGE_KEY = "stk_lang";

const dict = {
  // ---- common ----
  loading: { sw: "Inapakia...", en: "Loading...", fr: "Chargement..." },
  logout: { sw: "Logout", en: "Log out", fr: "Déconnexion" },
  save: { sw: "Hifadhi", en: "Save", fr: "Enregistrer" },
  saving: { sw: "Inahifadhi...", en: "Saving...", fr: "Enregistrement..." },
  cancel: { sw: "Ghairi", en: "Cancel", fr: "Annuler" },
  refresh: { sw: "Refresh", en: "Refresh", fr: "Actualiser" },
  send: { sw: "Tuma", en: "Send", fr: "Envoyer" },

  // ---- errors ----
  server_unreachable: {
    sw: "Seva haipatikani. Hakikisha backend (uvicorn) inaendesha.",
    en: "Can't reach the server. Make sure the backend (uvicorn) is running.",
    fr: "Serveur injoignable. Vérifiez que le backend (uvicorn) est en cours d'exécution.",
  },

  // ---- login / register ----
  phone_label: { sw: "Namba ya simu", en: "Phone number", fr: "Numéro de téléphone" },
  password_label: { sw: "Password", en: "Password", fr: "Mot de passe" },
  login_button: { sw: "Ingia", en: "Log in", fr: "Se connecter" },
  logging_in: { sw: "Inaingia...", en: "Logging in...", fr: "Connexion..." },
  no_account: { sw: "Huna akaunti?", en: "Don't have an account?", fr: "Vous n'avez pas de compte ?" },
  register_here: { sw: "Jisajili hapa", en: "Register here", fr: "Inscrivez-vous ici" },
  back_to_login: { sw: "Rudi kwenye login", en: "Back to login", fr: "Retour à la connexion" },

  register_resident_title: { sw: "Jisajili kama mkazi", en: "Register as a resident", fr: "S'inscrire comme résident" },
  register_resident_hint: {
    sw: "Location yako inatumika kuelekeza gari la taka nyumbani kwako.",
    en: "Your location is used to direct the waste truck to your home.",
    fr: "Votre position sert à diriger le camion à ordures jusque chez vous.",
  },
  register_submit: { sw: "Jisajili", en: "Register", fr: "S'inscrire" },
  registered_success: {
    sw: "Umesajiliwa. Sasa unaweza kuingia.",
    en: "You're registered. You can log in now.",
    fr: "Inscription réussie. Vous pouvez maintenant vous connecter.",
  },

  // ---- forms ----
  use_my_location: { sw: "Tumia location yangu ya sasa", en: "Use my current location", fr: "Utiliser ma position actuelle" },
  geo_unsupported: {
    sw: "Browser hii haina location.",
    en: "This browser doesn't support location.",
    fr: "Ce navigateur ne prend pas en charge la localisation.",
  },
  geo_failed: {
    sw: "Imeshindwa kupata location. Ruhusu location kwenye browser au uiandike mwenyewe.",
    en: "Couldn't get your location. Allow location access in the browser, or type it in yourself.",
    fr: "Impossible d'obtenir la position. Autorisez la localisation ou saisissez-la vous-même.",
  },
  saved_generic: { sw: "Imehifadhiwa.", en: "Saved.", fr: "Enregistré." },

  field_full_name: { sw: "Jina kamili", en: "Full name", fr: "Nom complet" },
  field_phone: { sw: "Namba ya simu", en: "Phone number", fr: "Numéro de téléphone" },
  field_password: {
    sw: "Password (angalau herufi 8)", en: "Password (at least 8 characters)", fr: "Mot de passe (8 caractères min.)",
  },
  field_ward: { sw: "Kata / Mtaa (ward)", en: "Ward / neighborhood", fr: "Quartier" },
  field_address: { sw: "Maelezo ya makazi (hiari)", en: "Address details (optional)", fr: "Détails de l'adresse (facultatif)" },
  field_latitude: { sw: "Latitude", en: "Latitude", fr: "Latitude" },
  field_longitude: { sw: "Longitude", en: "Longitude", fr: "Longitude" },
  field_driver_full_name: {
    sw: "Jina kamili la dereva / mwenye lori", en: "Driver / truck owner full name", fr: "Nom complet du chauffeur",
  },
  field_plate_number: { sw: "Namba ya lori", en: "Truck plate number", fr: "Plaque d'immatriculation du camion" },
  field_fuel_efficiency: {
    sw: "Matumizi ya mafuta (km kwa lita)", en: "Fuel efficiency (km per liter)", fr: "Consommation (km par litre)",
  },
  field_bin_code: {
    sw: "Bin code (ID ambayo sensor itatuma)", en: "Bin code (the ID the sensor will send)", fr: "Code du bac (ID envoyé par le capteur)",
  },

  // ---- resident dashboard ----
  welcome: { sw: "Karibu, {name}", en: "Welcome, {name}", fr: "Bienvenue, {name}" },
  no_customer_profile: {
    sw: "Akaunti hii haina wasifu wa mteja.", en: "This account has no customer profile.", fr: "Ce compte n'a pas de profil client.",
  },
  status_registered: { sw: "Umesajiliwa", en: "Registered", fr: "Inscrit" },
  status_billed: { sw: "Ada ya mwezi inasubiri malipo", en: "Monthly fee awaiting payment", fr: "Facture mensuelle en attente de paiement" },
  status_paid: { sw: "Umelipa. Gari litakuja kuchukua taka.", en: "Paid. The truck will come collect your waste.", fr: "Payé. Le camion viendra collecter vos ordures." },
  status_badge_registered: { sw: "registered", en: "registered", fr: "inscrit" },
  status_badge_billed: { sw: "billed", en: "billed", fr: "facturé" },
  status_badge_paid: { sw: "paid", en: "paid", fr: "payé" },
  monthly_fee_label: { sw: "Ada ya mwezi:", en: "Monthly fee:", fr: "Frais mensuels :" },
  complaint_title: { sw: "Toa maoni au malalamiko", en: "Send feedback or a complaint", fr: "Envoyer un avis ou une plainte" },
  service_rating_label: { sw: "Kiwango cha huduma", en: "Service rating", fr: "Note du service" },
  message_label: { sw: "Ujumbe", en: "Message", fr: "Message" },
  complaint_thanks: {
    sw: "Asante, maoni yako yamepokelewa.", en: "Thank you, your feedback has been received.", fr: "Merci, votre avis a bien été reçu.",
  },

  // ---- driver ----
  todays_route: { sw: "Route ya leo", en: "Today's route", fr: "Itinéraire du jour" },
  no_route_today: {
    sw: "Bado hujapewa route ya leo. Admin atatengeneza route baada ya wateja kulipa na bins kujaa.",
    en: "You don't have a route for today yet. The admin will generate one once customers pay and bins fill up.",
    fr: "Vous n'avez pas encore d'itinéraire aujourd'hui. L'administrateur en générera un une fois les clients payés et les bacs pleins.",
  },

  // ---- admin tabs ----
  tab_overview: { sw: "Overview", en: "Overview", fr: "Aperçu" },
  tab_residents: { sw: "Residents", en: "Residents", fr: "Résidents" },
  tab_register: { sw: "Register", en: "Register", fr: "Inscription" },
  tab_routes: { sw: "Routes (AI)", en: "Routes (AI)", fr: "Itinéraires (IA)" },
  tab_complaints: { sw: "Complaints", en: "Complaints", fr: "Plaintes" },
  tab_bins: { sw: "Bins", en: "Bins", fr: "Bacs" },
  tab_fleet: { sw: "Madereva/Malori", en: "Drivers & trucks", fr: "Chauffeurs et camions" },
  tab_admins: { sw: "Maadmin", en: "Admins", fr: "Administrateurs" },
  tab_providers: { sw: "Kanda (Providers)", en: "Zones (Providers)", fr: "Zones (Prestataires)" },
  tab_reports: { sw: "Ripoti", en: "Reports", fr: "Rapports" },

  // ---- overview ----
  live_map_title: { sw: "Ramani ya ukusanyaji (moja kwa moja)", en: "Live collection map", fr: "Carte de collecte en direct" },
  stat_residents: { sw: "Residents (waliolipa / jumla)", en: "Residents (paid / total)", fr: "Résidents (payé / total)" },
  stat_coverage: { sw: "Coverage", en: "Coverage", fr: "Couverture" },
  stat_revenue: { sw: "Mapato ya mwezi huu", en: "Revenue collected (this month)", fr: "Revenus collectés (ce mois-ci)" },
  stat_trucks: { sw: "Malori yanayofanya kazi", en: "Trucks in operation", fr: "Camions en service" },
  stat_cost_household: { sw: "Gharama / nyumba (leo)", en: "Cost / household (today)", fr: "Coût / foyer (aujourd'hui)" },
  stat_complaints: { sw: "Malalamiko yaliyopokelewa", en: "Complaints logged", fr: "Plaintes enregistrées" },
  legend_depot: { sw: "Depot", en: "Depot", fr: "Dépôt" },
  legend_registered: { sw: "Amesajiliwa (hajatumiwa bili)", en: "Registered (not billed yet)", fr: "Inscrit (pas encore facturé)" },
  legend_billed: { sw: "Ametumiwa bili", en: "Billed", fr: "Facturé" },
  legend_paid: { sw: "Amelipa", en: "Paid", fr: "Payé" },
  legend_full_bin: { sw: "Bin imejaa", en: "Full bin", fr: "Bac plein" },

  // ---- residents table ----
  search_placeholder: { sw: "Tafuta jina, simu au ward", en: "Search name, phone or ward", fr: "Rechercher nom, téléphone ou quartier" },
  status_all: { sw: "Status zote", en: "All statuses", fr: "Tous les statuts" },
  send_billing_all: { sw: "Tuma SMS ya bili kwa wote wasiolipa", en: "Send billing SMS to all unpaid", fr: "Envoyer le SMS de facturation aux impayés" },
  sending_ellipsis: { sw: "Inatuma...", en: "Sending...", fr: "Envoi en cours..." },
  show_removed: { sw: "Onyesha waliotolewa", en: "Show removed", fr: "Afficher les retirés" },
  confirm_remove: {
    sw: "Una uhakika unataka kumtoa {name} kwenye mfumo?",
    en: "Are you sure you want to remove {name} from the system?",
    fr: "Voulez-vous vraiment retirer {name} du système ?",
  },
  removed_notice: { sw: "{name} ametolewa kwenye mfumo.", en: "{name} has been removed from the system.", fr: "{name} a été retiré du système." },
  reactivated_notice: { sw: "{name} amerejeshwa kwenye mfumo.", en: "{name} has been restored to the system.", fr: "{name} a été rétabli dans le système." },
  th_name: { sw: "Jina", en: "Name", fr: "Nom" },
  th_phone: { sw: "Simu", en: "Phone", fr: "Téléphone" },
  th_ward: { sw: "Ward", en: "Ward", fr: "Quartier" },
  th_status: { sw: "Status", en: "Status", fr: "Statut" },
  th_actions: { sw: "Vitendo", en: "Actions", fr: "Actions" },
  removed_badge: { sw: "ametolewa", en: "removed", fr: "retiré" },
  reactivate_btn: { sw: "Mrejeshe", en: "Restore", fr: "Rétablir" },
  send_billing_one: { sw: "Tuma SMS ya bili", en: "Send billing SMS", fr: "Envoyer le SMS de facturation" },
  edit_btn: { sw: "Hariri", en: "Edit", fr: "Modifier" },
  remove_btn: { sw: "Toa", en: "Remove", fr: "Retirer" },
  no_customers: { sw: "Hakuna wateja.", en: "No customers.", fr: "Aucun client." },
  billing_sent_count: { sw: "SMS zimetumwa: {n}", en: "SMS sent: {n}", fr: "SMS envoyés : {n}" },
  billing_failed_count: { sw: "zimeshindwa: {n}", en: "failed: {n}", fr: "échecs : {n}" },
  billing_already_sent: { sw: "tayari zilitumwa mwezi huu: {n}", en: "already sent this month: {n}", fr: "déjà envoyés ce mois-ci : {n}" },
  billing_skipped_paid: { sw: "wamelipa tayari: {n}", en: "already paid: {n}", fr: "déjà payé : {n}" },
  billing_error_prefix: { sw: "Kosa: {err}", en: "Error: {err}", fr: "Erreur : {err}" },
  billing_mock_note: {
    sw: "(Mock: SMS zinaonekana kwenye terminal ya seva, hazijatumwa kweli.)",
    en: "(Mock: SMS appear in the server terminal, they aren't really sent.)",
    fr: "(Simulation : les SMS s'affichent dans le terminal du serveur, ils ne sont pas réellement envoyés.)",
  },

  // ---- register (admin) ----
  register_customer_title: { sw: "Sajili mteja", en: "Register customer", fr: "Inscrire un client" },
  register_customer_submit: { sw: "Sajili mteja", en: "Register customer", fr: "Inscrire le client" },
  register_customer_success: { sw: "Mteja amesajiliwa (ID {id}).", en: "Customer registered (ID {id}).", fr: "Client inscrit (ID {id})." },
  register_driver_title: { sw: "Sajili dereva / mwenye lori", en: "Register driver / truck owner", fr: "Inscrire un chauffeur / propriétaire de camion" },
  register_driver_hint: {
    sw: "Inatengeneza login ya dereva na lori lake kwa pamoja.",
    en: "Creates the driver's login and their truck together.",
    fr: "Crée en même temps le compte du chauffeur et son camion.",
  },
  register_driver_submit: { sw: "Sajili dereva na lori", en: "Register driver and truck", fr: "Inscrire le chauffeur et le camion" },
  register_driver_success: { sw: "Dereva amesajiliwa na lori {plate}.", en: "Driver registered with truck {plate}.", fr: "Chauffeur inscrit avec le camion {plate}." },
  register_bin_title: { sw: "Sajili bin", en: "Register bin", fr: "Inscrire un bac" },
  register_bin_hint: {
    sw: "Bin code ndiyo ID ambayo sensor itatuma kwenye /sensors/readings.",
    en: "The bin code is the ID the sensor will send to /sensors/readings.",
    fr: "Le code du bac est l'identifiant que le capteur enverra à /sensors/readings.",
  },
  register_bin_submit: { sw: "Sajili bin", en: "Register bin", fr: "Inscrire le bac" },
  register_bin_success: { sw: "Bin {code} imesajiliwa.", en: "Bin {code} registered.", fr: "Bac {code} inscrit." },

  // ---- routes (admin) ----
  generate_routes_btn: { sw: "Tengeneza routes (AI)", en: "Generate routes (AI)", fr: "Générer les itinéraires (IA)" },
  calculating: { sw: "Inahesabu...", en: "Calculating...", fr: "Calcul en cours..." },
  source_osrm: { sw: "Umbali na muda vimetoka OSRM (ramani za barabara halisi).", en: "Distance and time came from OSRM (real road routing).", fr: "La distance et la durée proviennent d'OSRM (itinéraire routier réel)." },
  source_estimate: {
    sw: "Umbali ni makadirio ya mstari-wa-moja, si OSRM: {source}",
    en: "Distance is a straight-line estimate, not OSRM: {source}",
    fr: "La distance est une estimation à vol d'oiseau, pas OSRM : {source}",
  },
  no_routes_today: {
    sw: "Hakuna route kwa siku hii. Bonyeza Generate baada ya wateja kulipa au bin kujaa.",
    en: "No route for this day yet. Click Generate once customers have paid or a bin is full.",
    fr: "Aucun itinéraire pour ce jour. Cliquez sur Générer une fois des clients payés ou un bac plein.",
  },

  // ---- route view (shared by driver + admin) ----
  truck_label: { sw: "Lori {plate}", en: "Truck {plate}", fr: "Camion {plate}" },
  driver_label: { sw: "Dereva:", en: "Driver:", fr: "Chauffeur :" },
  stops_label: { sw: "Vituo:", en: "Stops:", fr: "Arrêts :" },
  distance_label: { sw: "Umbali", en: "Distance", fr: "Distance" },
  est_time_label: { sw: "Muda unaokadiriwa", en: "Estimated time", fr: "Durée estimée" },
  fuel_label: { sw: "Mafuta", en: "Fuel", fr: "Carburant" },
  trip_cost_label: { sw: "Gharama ya safari", en: "Trip cost", fr: "Coût du trajet" },
  legend_household_paid: { sw: "Nyumba (imelipa)", en: "Household (paid)", fr: "Foyer (payé)" },
  legend_bin_full_route: { sw: "Bin imejaa", en: "Full bin", fr: "Bac plein" },
  legend_completed: { sw: "Imekamilika", en: "Completed", fr: "Terminé" },
  bin_label: { sw: "Bin", en: "Bin", fr: "Bac" },
  household_label: { sw: "Nyumba", en: "Household", fr: "Foyer" },
  filled_percent: { sw: "{pct}% imejaa", en: "{pct}% full", fr: "{pct}% plein" },
  completed_status: { sw: "Imekamilika", en: "Completed", fr: "Terminé" },
  map_link: { sw: "Ramani", en: "Map", fr: "Carte" },

  // ---- complaints (admin) ----
  th_date: { sw: "Tarehe", en: "Date", fr: "Date" },
  th_customer: { sw: "Mteja", en: "Customer", fr: "Client" },
  th_rating: { sw: "Kiwango", en: "Rating", fr: "Note" },
  th_message: { sw: "Ujumbe", en: "Message", fr: "Message" },
  no_complaints: { sw: "Hakuna malalamiko bado.", en: "No complaints yet.", fr: "Aucune plainte pour le moment." },

  // ---- payment button ----
  pay_button: { sw: "Lipa", en: "Make payment", fr: "Payer" },
  pay_sending: { sw: "Inatuma ombi...", en: "Sending request...", fr: "Envoi de la demande..." },
  pay_waiting: {
    sw: "Angalia simu yako, weka PIN kukamilisha malipo",
    en: "Check your phone, enter your PIN to complete payment",
    fr: "Vérifiez votre téléphone, entrez votre code PIN pour finaliser le paiement",
  },
  pay_paid: { sw: "Amelipa", en: "Paid", fr: "Payé" },
  pay_failed: { sw: "Malipo hayakukamilika. Jaribu tena.", en: "Payment didn't go through. Try again.", fr: "Le paiement a échoué. Réessayez." },
  pay_review: {
    sw: "Kiasi kilicholipwa hakilingani. Admin ahakiki malipo haya.",
    en: "The amount paid doesn't match. An admin will review this payment.",
    fr: "Le montant payé ne correspond pas. Un administrateur va vérifier ce paiement.",
  },
  pay_timeout: { sw: "Bado hatujapata jibu la malipo.", en: "We haven't heard back about this payment yet.", fr: "Nous n'avons pas encore de réponse pour ce paiement." },
  pay_retry: { sw: "Jaribu tena", en: "Try again", fr: "Réessayer" },
  pay_recheck: { sw: "Angalia tena", en: "Check again", fr: "Vérifier à nouveau" },

  // ---- admin: bins management ----
  bins_registered_label: { sw: "Bins zilizosajiliwa", en: "Registered bins", fr: "Bacs inscrits" },
  th_code: { sw: "Code", en: "Code", fr: "Code" },
  th_location: { sw: "Mahali", en: "Location", fr: "Emplacement" },
  th_fill: { sw: "Kujaa", en: "Fill level", fr: "Remplissage" },
  bin_status_full: { sw: "imejaa", en: "full", fr: "plein" },
  bin_status_ok: { sw: "sawa", en: "ok", fr: "ok" },
  open_map: { sw: "Ramani", en: "Map", fr: "Carte" },
  no_bins: { sw: "Hakuna bin zilizosajiliwa.", en: "No bins registered.", fr: "Aucun bac inscrit." },
  bin_edit_hint: {
    sw: "Code ya bin haibadilishwi kwa sababu sensor inaitumia. Unaweza kubadilisha mahali ilipo tu.",
    en: "A bin's code can't be changed because its sensor uses it. You can change where it is.",
    fr: "Le code d'un bac ne peut pas être modifié car son capteur l'utilise. Vous pouvez changer son emplacement.",
  },
  confirm_remove_bin: {
    sw: "Kuondoa bin {code} (mfano imeondolewa mahali pake)? Haitaonekana tena kwenye ramani wala routes.",
    en: "Remove bin {code} (e.g. it was taken away)? It will no longer appear on the map or in routes.",
    fr: "Retirer le bac {code} (par ex. enlevé) ? Il n'apparaîtra plus sur la carte ni dans les itinéraires.",
  },
  bin_removed_notice: { sw: "Bin {code} imeondolewa.", en: "Bin {code} was removed.", fr: "Le bac {code} a été retiré." },
  bin_restored_notice: { sw: "Bin {code} imerejeshwa.", en: "Bin {code} was restored.", fr: "Le bac {code} a été rétabli." },
  bin_saved_notice: { sw: "Bin {code} imehifadhiwa.", en: "Bin {code} updated.", fr: "Bac {code} mis à jour." },

  // ---- admin: drivers & trucks ----
  fleet_active_label: { sw: "Madereva/malori yanayofanya kazi", en: "Active drivers/trucks", fr: "Chauffeurs/camions actifs" },
  fleet_register_hint: {
    sw: "Kusajili dereva/lori mpya, tumia kichupo cha Register.",
    en: "To add a new driver/truck, use the Register tab.",
    fr: "Pour ajouter un chauffeur/camion, utilisez l'onglet Inscription.",
  },
  th_driver: { sw: "Dereva", en: "Driver", fr: "Chauffeur" },
  th_truck: { sw: "Lori", en: "Truck", fr: "Camion" },
  th_fuel: { sw: "Km kwa lita", en: "Km per litre", fr: "Km par litre" },
  no_drivers: { sw: "Hakuna dereva aliyesajiliwa.", en: "No drivers registered.", fr: "Aucun chauffeur inscrit." },
  confirm_remove_driver: {
    sw: "Kumtoa {name} kunafunga akaunti yake na lori {plate} halitatumika kwenye routes. Endelea?",
    en: "Removing {name} disables their login, and truck {plate} will no longer be used for routes. Continue?",
    fr: "Retirer {name} désactive son compte et le camion {plate} ne sera plus utilisé. Continuer ?",
  },
  driver_removed_notice: {
    sw: "Dereva {name} ameondolewa. Tengeneza routes upya.",
    en: "Driver {name} was removed. Regenerate the routes.",
    fr: "Le chauffeur {name} a été retiré. Régénérez les itinéraires.",
  },

  // ---- admin: managing other admins (super admin only) ----
  admins_add_title: { sw: "Ongeza admin mpya", en: "Add a new admin", fr: "Ajouter un administrateur" },
  admins_add_hint: {
    sw: "Admin mpya anaweza kufanya kila kitu isipokuwa kuongeza au kuondoa admin wengine. Ni wewe tu (Super Admin) unayeweza kufanya hivyo.",
    en: "A new admin can do everything except add or remove other admins. Only you (the Super Admin) can do that.",
    fr: "Un nouvel administrateur peut tout faire sauf ajouter ou retirer d'autres administrateurs. Seul vous (Super Admin) le pouvez.",
  },
  admins_add_submit: { sw: "Ongeza admin", en: "Add admin", fr: "Ajouter l'administrateur" },
  admins_add_success: { sw: "Admin {name} ameongezwa.", en: "Admin {name} added.", fr: "Administrateur {name} ajouté." },
  th_role: { sw: "Cheo", en: "Role", fr: "Rôle" },
  role_super_admin: { sw: "Super Admin", en: "Super Admin", fr: "Super Admin" },
  role_admin: { sw: "Admin", en: "Admin", fr: "Admin" },
  confirm_remove_admin: {
    sw: "Kumtoa {name} kunamzuia kuingia kwenye mfumo mara moja. Endelea?",
    en: "Removing {name} locks them out of the system immediately. Continue?",
    fr: "Retirer {name} le bloque immédiatement. Continuer ?",
  },
  admin_removed_notice: { sw: "{name} ametolewa uadmin.", en: "{name} is no longer an admin.", fr: "{name} n'est plus administrateur." },
  admin_restored_notice: { sw: "{name} amerudishwa uadmin.", en: "{name} is an admin again.", fr: "{name} est de nouveau administrateur." },

  // ---- admin: marking routes complete ----
  complete_route_btn: { sw: "Kamilisha route yote", en: "Mark whole route complete", fr: "Terminer tout l'itinéraire" },
  confirm_complete_route: {
    sw: "Hii itaweka vituo vyote vilivyobaki kama vimekusanywa na kufunga route hii. Endelea?",
    en: "This marks every remaining stop as collected and closes the route. Continue?",
    fr: "Cela marque tous les arrêts restants comme collectés et clôture l'itinéraire. Continuer ?",
  },

  // ---- admin: service providers (zones) ----
  providers_add_title: { sw: "Ongeza kanda mpya", en: "Add a new zone", fr: "Ajouter une nouvelle zone" },
  providers_add_hint: {
    sw: "Kila kanda ina kituo (depot) chake, bei yake ya mafuta, malori na wateja wake wenyewe. Baada ya kuunda kanda, ongeza admin wake wa kwanza kwenye tab ya Admins.",
    en: "Each zone has its own depot, fuel price, trucks and customers. After creating a zone, add its first admin from the Admins tab.",
    fr: "Chaque zone a son propre dépôt, prix du carburant, camions et clients. Après avoir créé une zone, ajoutez son premier administrateur dans l'onglet Admins.",
  },
  providers_add_submit: { sw: "Ongeza kanda", en: "Add zone", fr: "Ajouter la zone" },
  providers_add_success: { sw: "Kanda {name} imeongezwa.", en: "Zone {name} added.", fr: "Zone {name} ajoutée." },
  field_zone_name: { sw: "Jina la kanda (mfano: Dar es Salaam)", en: "Zone name (e.g. Dar es Salaam)", fr: "Nom de la zone (ex. Dar es Salaam)" },
  field_fuel_price: { sw: "Bei ya mafuta (TZS kwa lita)", en: "Fuel price (TZS per litre)", fr: "Prix du carburant (TZS par litre)" },
  field_zone: { sw: "Kanda", en: "Zone", fr: "Zone" },
  field_zone_placeholder: { sw: "-- chagua kanda --", en: "-- choose a zone --", fr: "-- choisir une zone --" },
  th_zone: { sw: "Kanda", en: "Zone", fr: "Zone" },
  th_customers: { sw: "Wateja", en: "Customers", fr: "Clients" },
  th_bins: { sw: "Bins", en: "Bins", fr: "Bacs" },
  th_trucks: { sw: "Malori", en: "Trucks", fr: "Camions" },
  th_revenue_this_month: { sw: "Mapato mwezi huu", en: "Revenue this month", fr: "Recettes ce mois-ci" },
  th_fuel_price: { sw: "Bei ya mafuta", en: "Fuel price", fr: "Prix du carburant" },
  no_providers: { sw: "Hakuna kanda bado.", en: "No zones yet.", fr: "Aucune zone pour le moment." },

  // ---- admin: reports ----
  granularity_month: { sw: "Kila mwezi", en: "Monthly", fr: "Mensuel" },
  granularity_quarter: { sw: "Robo mwaka", en: "Quarterly", fr: "Trimestriel" },
  granularity_year: { sw: "Kila mwaka", en: "Annually", fr: "Annuel" },
  reports_my_zone_title: { sw: "Makusanyo ya kanda yako", en: "Your zone's collections", fr: "Recettes de votre zone" },
  reports_all_zones_title: { sw: "Makusanyo ya kanda zote", en: "Collections across all zones", fr: "Recettes de toutes les zones" },
  no_report_data: { sw: "Bado hakuna malipo ya kuonyesha.", en: "No payments to show yet.", fr: "Aucun paiement à afficher pour le moment." },
  payments_count_label: { sw: "malipo {n}", en: "{n} payments", fr: "{n} paiements" },
  th_total_collected: { sw: "Jumla iliyokusanywa", en: "Total collected", fr: "Total collecté" },

  // ---- resident: payment history / receipts ----
  payment_history_title: { sw: "Historia ya malipo yangu", en: "My payment history", fr: "Mon historique de paiement" },
  no_payments_yet: { sw: "Bado hujalipa.", en: "No payments yet.", fr: "Aucun paiement pour le moment." },
  th_period: { sw: "Mwezi", en: "Period", fr: "Période" },
  th_amount: { sw: "Kiasi", en: "Amount", fr: "Montant" },
  download_receipt_btn: { sw: "Pakua risiti", en: "Download receipt", fr: "Télécharger le reçu" },

  // ---- password self-service ----
  change_password_link: { sw: "Badilisha password", en: "Change password", fr: "Changer le mot de passe" },
  change_password_title: { sw: "Badilisha password yako", en: "Change your password", fr: "Changer votre mot de passe" },
  current_password_label: { sw: "Password ya sasa", en: "Current password", fr: "Mot de passe actuel" },
  new_password_label: { sw: "Password mpya", en: "New password", fr: "Nouveau mot de passe" },
  confirm_password_label: { sw: "Rudia password mpya", en: "Confirm new password", fr: "Confirmez le nouveau mot de passe" },
  change_password_submit: { sw: "Badilisha password", en: "Change password", fr: "Changer le mot de passe" },
  passwords_dont_match: { sw: "Password mpya hazifanani.", en: "The new passwords don't match.", fr: "Les nouveaux mots de passe ne correspondent pas." },
  password_changed_success: { sw: "Password imebadilishwa.", en: "Password changed.", fr: "Mot de passe changé." },
  back_to_dashboard: { sw: "Rudi kwenye dashibodi", en: "Back to dashboard", fr: "Retour au tableau de bord" },

  forgot_password_link: { sw: "Umesahau password?", en: "Forgot password?", fr: "Mot de passe oublié ?" },
  forgot_password_title: { sw: "Umesahau password", en: "Forgot password", fr: "Mot de passe oublié" },
  forgot_password_hint: {
    sw: "Weka namba ya simu uliyosajili. Tutakutumia msimbo wa siri (SMS) wa kubadili password.",
    en: "Enter the phone number you registered with. We'll text you a code to reset your password.",
    fr: "Entrez le numéro avec lequel vous êtes inscrit. Nous vous enverrons un code par SMS.",
  },
  send_code_btn: { sw: "Tuma msimbo", en: "Send code", fr: "Envoyer le code" },
  otp_sent_notice: { sw: "Msimbo umetumwa kwa SMS. Angalia simu yako.", en: "A code has been texted to you. Check your phone.", fr: "Un code vous a été envoyé par SMS. Vérifiez votre téléphone." },
  otp_code_label: { sw: "Msimbo (herufi 6)", en: "Code (6 digits)", fr: "Code (6 chiffres)" },
  reset_password_submit: { sw: "Weka password mpya", en: "Reset password", fr: "Réinitialiser le mot de passe" },
  password_reset_success: { sw: "Password imebadilishwa. Sasa unaweza kuingia.", en: "Password reset. You can log in now.", fr: "Mot de passe réinitialisé. Vous pouvez maintenant vous connecter." },

  // ---- fuel price ----
  fuel_price_card_title: { sw: "Bei ya mafuta ya kanda yako", en: "Your zone's fuel price", fr: "Prix du carburant de votre zone" },
  fuel_price_updated: { sw: "Bei ya mafuta imesasishwa.", en: "Fuel price updated.", fr: "Prix du carburant mis à jour." },
  liter_short: { sw: "lita", en: "litre", fr: "litre" },

  // ---- v4: reports/pdf, webhook logs, wallet, phone-override ----
  download_pdf_btn: { sw: "Pakua PDF", en: "Download PDF", fr: "Télécharger le PDF" },
  download_statement_btn: { sw: "Pakua taarifa", en: "Download statement", fr: "Télécharger le relevé" },
  webhook_logs_title: { sw: "Mapokezi ya Payment Provider (webhook)", en: "Payment provider webhook logs", fr: "Journaux webhook du fournisseur de paiement" },
  show_btn: { sw: "Onyesha", en: "Show", fr: "Afficher" },
  th_time: { sw: "Muda", en: "Time", fr: "Heure" },
  th_order_id: { sw: "Order ID", en: "Order ID", fr: "Order ID" },
  th_error: { sw: "Hitilafu", en: "Error", fr: "Erreur" },
  webhook_processed: { sw: "imechakatwa", en: "processed", fr: "traité" },
  webhook_not_processed: { sw: "haijachakatwa", en: "not processed", fr: "non traité" },
  no_webhook_logs: { sw: "Hakuna mapokezi bado.", en: "No webhook calls yet.", fr: "Aucun appel webhook pour le moment." },

  pay_different_phone_link: { sw: "Lipa kwa namba nyingine?", en: "Pay from a different phone?", fr: "Payer depuis un autre numéro ?" },

  wallet_title: { sw: "Wallet yangu", en: "My wallet", fr: "Mon portefeuille" },
  wallet_balance_label: { sw: "salio la sasa", en: "current balance", fr: "solde actuel" },
  topup_amount_placeholder: { sw: "Kiasi (TZS)", en: "Amount (TZS)", fr: "Montant (TZS)" },
  topup_submit_btn: { sw: "Ongeza kwenye wallet", en: "Add to wallet", fr: "Ajouter au portefeuille" },
  pay_from_wallet_btn: { sw: "Lipa kutoka wallet", en: "Pay from wallet", fr: "Payer depuis le portefeuille" },
  paid_from_wallet_success: { sw: "Imelipwa kwa mafanikio kutoka wallet.", en: "Paid successfully from your wallet.", fr: "Payé avec succès depuis votre portefeuille." },
  wallet_topup_label: { sw: "Kuongeza kwenye wallet", en: "Wallet top-up", fr: "Recharge du portefeuille" },
};

let currentLang = (typeof localStorage !== "undefined" && localStorage.getItem(STORAGE_KEY)) || "sw";
const listeners = new Set();

export function getLang() {
  return currentLang;
}

export function setLang(lang) {
  if (!LANGUAGES[lang] || lang === currentLang) return;
  currentLang = lang;
  localStorage.setItem(STORAGE_KEY, lang);
  listeners.forEach((fn) => fn());
}

export function subscribe(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

// t("welcome", {name: "Amina"}) -> "Karibu, Amina" (in whichever language is active)
export function t(key, vars) {
  const entry = dict[key];
  let s = entry ? entry[currentLang] || entry.sw || key : key;
  if (vars) for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, v);
  return s;
}
