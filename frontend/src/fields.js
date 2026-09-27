// Field lists for the registration forms (used by admin and by self-registration).
// labelKey is looked up via t() in FormCard, so these forms follow the chosen language.
export const customerFields = [
  { name: "full_name", labelKey: "field_full_name", required: true },
  { name: "phone", labelKey: "field_phone", type: "tel", placeholder: "0712345678", required: true },
  { name: "password", labelKey: "field_password", type: "password", required: true },
  { name: "ward", labelKey: "field_ward", required: true },
  { name: "address", labelKey: "field_address" },
  { name: "latitude", labelKey: "field_latitude", type: "number", step: "any", required: true },
  { name: "longitude", labelKey: "field_longitude", type: "number", step: "any", required: true },
];

export const driverFields = [
  { name: "full_name", labelKey: "field_driver_full_name", required: true },
  { name: "phone", labelKey: "field_phone", type: "tel", placeholder: "0712345678", required: true },
  { name: "password", labelKey: "field_password", type: "password", required: true },
  { name: "plate_number", labelKey: "field_plate_number", placeholder: "T 123 ABC", required: true },
  { name: "fuel_km_per_liter", labelKey: "field_fuel_efficiency", type: "number", step: "0.1", required: true },
];

export const binFields = [
  { name: "code", labelKey: "field_bin_code", placeholder: "BIN-001", required: true },
  { name: "ward", labelKey: "field_ward", required: true },
  { name: "latitude", labelKey: "field_latitude", type: "number", step: "any", required: true },
  { name: "longitude", labelKey: "field_longitude", type: "number", step: "any", required: true },
];
