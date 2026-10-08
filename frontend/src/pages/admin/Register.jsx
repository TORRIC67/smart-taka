import FormCard from "../../components/FormCard.jsx";
import { binFields, customerFields, driverFields } from "../../fields.js";
import { post } from "../../api/client";
import { useI18n } from "../../useI18n";

// The admin registers customers, drivers (with their truck) and bins.
// category/monthly_fee_tzs are admin-only, so they're added here - not in the shared
// customerFields list, which SelfRegister.jsx (residents signing themselves up) also uses.
const adminCustomerFields = [
  ...customerFields,
  {
    name: "category", labelKey: "field_customer_category", type: "select", required: true,
    options: [{ value: "residential", label: "" }, { value: "institution", label: "" }],
    optionLabelKeys: { residential: "category_residential", institution: "category_institution" },
  },
  { name: "monthly_fee_tzs", labelKey: "field_custom_fee", type: "number", placeholder_key: "field_custom_fee_placeholder" },
];

// The admin registers customers, drivers (with their truck) and bins
export default function Register() {
  const { t } = useI18n();
  const customerFieldsLocalized = adminCustomerFields.map((f) =>
    f.name === "category"
      ? { ...f, options: f.options.map((o) => ({ ...o, label: t(f.optionLabelKeys[o.value]) })) }
      : f.name === "monthly_fee_tzs"
      ? { ...f, placeholder: t("field_custom_fee_placeholder") }
      : f
  );
  return (
    <>
      <FormCard
        title={t("register_customer_title")}
        hint={t("register_customer_hint")}
        fields={customerFieldsLocalized}
        withLocation
        submitLabel={t("register_customer_submit")}
        onSubmit={async (v) => {
          if (!v.monthly_fee_tzs) delete v.monthly_fee_tzs; // blank = use the zone's standard fee
          return t("register_customer_success", { id: (await post("/admin/customers", v)).id });
        }}
      />
      <FormCard
        title={t("register_driver_title")}
        hint={t("register_driver_hint")}
        fields={driverFields}
        submitLabel={t("register_driver_submit")}
        onSubmit={async (v) => {
          const r = await post("/admin/drivers", v);
          return t("register_driver_success", { plate: r.plate_number });
        }}
      />
      <FormCard
        title={t("register_bin_title")}
        hint={t("register_bin_hint")}
        fields={binFields}
        withLocation
        submitLabel={t("register_bin_submit")}
        onSubmit={async (v) => t("register_bin_success", { code: (await post("/admin/bins", v)).code })}
      />
    </>
  );
}
