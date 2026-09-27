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
