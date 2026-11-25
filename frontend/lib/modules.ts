export type Field = {
  name: string;
  label: string;
  kind?: "text" | "number" | "date" | "datetime-local" | "textarea" | "json" | "select" | "file";
  required?: boolean;
  options?: string[];
};

export type ModuleSpec = {
  key: string;
  label: string;
  description: string;
  group: string;
  fields: Field[];
  columns: string[];
  roles?: string[];
  visibleRoles?: string[];
};

const member = { name: "member", label: "Member ID", kind: "number" as const, required: true };
const packageId = { name: "package", label: "Package ID", kind: "number" as const, required: true };

export const modules: ModuleSpec[] = [
  { key: "members", label: "Members", description: "Member profiles, contacts and QR IDs", group: "People", columns: ["id", "user", "phone", "joined_at", "active", "qr_id"], fields: [
    { name: "user_id", label: "Member user ID", kind: "number", required: true }, { name: "phone", label: "Phone" },
    { name: "date_of_birth", label: "Date of birth", kind: "date" }, { name: "emergency_contact_name", label: "Emergency contact" },
    { name: "emergency_contact_phone", label: "Emergency phone" }, { name: "photo", label: "Profile photo", kind: "file" },
    { name: "document", label: "Member document", kind: "file" },
  ], roles: ["admin", "receptionist"], visibleRoles: ["admin", "receptionist", "trainer", "member"] },
  { key: "staff", label: "Trainers & staff", description: "Team profiles, specialties and schedules", group: "People", columns: ["id", "user", "title", "specialties", "active"], fields: [
    { name: "user_id", label: "Staff user ID", kind: "number", required: true }, { name: "title", label: "Role / title", required: true },
    { name: "phone", label: "Phone" }, { name: "specialties", label: "Specialties" }, { name: "schedule", label: "Schedule JSON", kind: "json" },
  ], roles: ["admin"], visibleRoles: ["admin", "receptionist", "trainer"] },
  { key: "packages", label: "Packages", description: "Membership products and pricing", group: "Operations", columns: ["id", "name", "duration_days", "price", "active"], fields: [
    { name: "name", label: "Package name", required: true }, { name: "description", label: "Description", kind: "textarea" },
    { name: "duration_days", label: "Duration in days", kind: "number", required: true }, { name: "price", label: "Price", kind: "number", required: true },
  ], roles: ["admin"], visibleRoles: ["admin", "receptionist", "trainer", "member"] },
  { key: "memberships", label: "Memberships", description: "Subscriptions, renewals and freeze status", group: "Operations", columns: ["id", "member_name", "package_name", "start_date", "end_date", "status"], fields: [
    member, packageId, { name: "start_date", label: "Starts", kind: "date", required: true }, { name: "end_date", label: "Ends", kind: "date", required: true },
    { name: "status", label: "Status", kind: "select", options: ["active", "frozen", "cancelled", "expired"] }, { name: "notes", label: "Notes", kind: "textarea" },
  ], roles: ["admin", "receptionist"], visibleRoles: ["admin", "receptionist", "trainer", "member"] },
  { key: "attendance", label: "Attendance", description: "QR check-in/out and visit history", group: "Operations", columns: ["id", "member_name", "checked_in_at", "checked_out_at", "source"], fields: [
    member, { name: "source", label: "Source" },
  ], roles: ["admin", "receptionist"], visibleRoles: ["admin", "receptionist", "trainer", "member"] },
  { key: "classes", label: "Classes", description: "Schedules, capacity and trainer assignments", group: "Operations", columns: ["id", "name", "trainer_name", "starts_at", "capacity", "booked_count"], fields: [
    { name: "name", label: "Class name", required: true }, { name: "trainer", label: "Trainer staff ID", kind: "number" },
    { name: "starts_at", label: "Starts at", kind: "datetime-local", required: true }, { name: "ends_at", label: "Ends at", kind: "datetime-local", required: true },
    { name: "capacity", label: "Capacity", kind: "number", required: true }, { name: "location", label: "Location" },
    { name: "description", label: "Description", kind: "textarea" },
  ], roles: ["admin", "receptionist", "trainer"], visibleRoles: ["admin", "receptionist", "trainer", "member"] },
  { key: "bookings", label: "Class bookings", description: "Reservations with capacity and duplicate protection", group: "Operations", columns: ["id", "class_name", "member_name", "status", "booked_at"], fields: [
    { name: "gym_class", label: "Class ID", kind: "number", required: true }, member,
    { name: "status", label: "Status", kind: "select", options: ["booked", "cancelled", "attended"] },
  ], roles: ["admin", "receptionist", "trainer", "member"], visibleRoles: ["admin", "receptionist", "trainer", "member"] },
  { key: "payments", label: "Payments", description: "Receipts, transaction references and revenue", group: "Finance", columns: ["id", "member_name", "amount", "method", "reference", "paid_at"], fields: [
    member, { name: "membership", label: "Membership ID", kind: "number" }, { name: "amount", label: "Amount", kind: "number", required: true },
    { name: "method", label: "Method", kind: "select", options: ["cash", "card", "bank", "online"], required: true },
    { name: "reference", label: "Payment reference" }, { name: "notes", label: "Notes", kind: "textarea" },
  ], roles: ["admin", "receptionist"], visibleRoles: ["admin", "receptionist", "trainer", "member"] },
  { key: "workouts", label: "Workout plans", description: "Personalized training blocks and exercise details", group: "Training", columns: ["id", "name", "member_name", "trainer", "start_date", "active"], fields: [
    member, { name: "trainer", label: "Trainer staff ID", kind: "number" }, { name: "name", label: "Plan name", required: true },
    { name: "details", label: "Exercise plan JSON", kind: "json" }, { name: "start_date", label: "Starts", kind: "date" },
    { name: "end_date", label: "Ends", kind: "date" },
  ], roles: ["admin", "trainer"], visibleRoles: ["admin", "trainer", "member"] },
  { key: "workout-logs", label: "Workout history", description: "Log exercise sets, reps and working weights", group: "Training", columns: ["id", "member_name", "exercise_name", "performed_at", "sets", "reps", "weight_kg"], fields: [
    member, { name: "plan", label: "Plan ID", kind: "number" }, { name: "exercise_name", label: "Exercise", required: true },
    { name: "performed_at", label: "Date", kind: "date" }, { name: "sets", label: "Sets", kind: "number", required: true },
    { name: "reps", label: "Reps", kind: "number", required: true }, { name: "weight_kg", label: "Weight kg", kind: "number" },
    { name: "notes", label: "Notes", kind: "textarea" },
  ], roles: ["admin", "trainer", "member"], visibleRoles: ["admin", "trainer", "member"] },
  { key: "exercises", label: "Exercise library", description: "Exercise catalog by muscle group and equipment", group: "Training", columns: ["id", "name", "muscle_group", "equipment"], fields: [
    { name: "name", label: "Exercise", required: true }, { name: "muscle_group", label: "Muscle group", required: true },
    { name: "equipment", label: "Equipment" }, { name: "instructions", label: "Instructions", kind: "textarea" },
  ], roles: ["admin", "trainer"], visibleRoles: ["admin", "trainer", "member"] },
  { key: "meals", label: "Nutrition plans", description: "Meal plans, calories and macronutrients", group: "Training", columns: ["id", "name", "member_name", "daily_calories", "protein_g", "start_date"], fields: [
    member, { name: "trainer", label: "Trainer staff ID", kind: "number" }, { name: "name", label: "Plan name", required: true },
    { name: "meals", label: "Meals JSON", kind: "json" }, { name: "daily_calories", label: "Calories / day", kind: "number" },
    { name: "protein_g", label: "Protein g", kind: "number" }, { name: "carbs_g", label: "Carbs g", kind: "number" },
    { name: "fats_g", label: "Fat g", kind: "number" }, { name: "start_date", label: "Starts", kind: "date" },
    { name: "end_date", label: "Ends", kind: "date" },
  ], roles: ["admin", "trainer"], visibleRoles: ["admin", "trainer", "member"] },
  { key: "nutrition-logs", label: "Food diary", description: "Track meals and daily calories and macros", group: "Training", columns: ["id", "member_name", "meal_name", "logged_at", "calories", "protein_g", "carbs_g", "fats_g"], fields: [
    member, { name: "meal_name", label: "Meal", required: true }, { name: "food_entries", label: "Food items JSON", kind: "json" },
    { name: "logged_at", label: "Date", kind: "date" }, { name: "calories", label: "Calories", kind: "number" },
    { name: "protein_g", label: "Protein g", kind: "number" }, { name: "carbs_g", label: "Carbs g", kind: "number" },
    { name: "fats_g", label: "Fat g", kind: "number" }, { name: "notes", label: "Notes", kind: "textarea" },
  ], roles: ["admin", "receptionist", "trainer", "member"], visibleRoles: ["admin", "receptionist", "trainer", "member"] },
  { key: "progress", label: "Fitness progress", description: "Measurements, goals and computed BMI history", group: "Training", columns: ["id", "member_name", "recorded_at", "weight_kg", "body_fat_percent", "bmi"], fields: [
    member, { name: "recorded_at", label: "Recorded date", kind: "date" }, { name: "weight_kg", label: "Weight kg", kind: "number" },
    { name: "height_cm", label: "Height cm", kind: "number" }, { name: "body_fat_percent", label: "Body fat %", kind: "number" },
    { name: "measurements", label: "Measurements JSON", kind: "json" }, { name: "goal", label: "Goal", kind: "textarea" },
    { name: "photo", label: "Progress photo", kind: "file" },
  ], roles: ["admin", "receptionist", "trainer"], visibleRoles: ["admin", "receptionist", "trainer", "member"] },
  { key: "equipment", label: "Equipment", description: "Inventory, condition and maintenance dates", group: "Operations", columns: ["id", "name", "inventory_code", "quantity", "status", "maintenance_due"], fields: [
    { name: "name", label: "Equipment", required: true }, { name: "inventory_code", label: "Inventory code", required: true },
    { name: "quantity", label: "Quantity", kind: "number" }, { name: "status", label: "Status", kind: "select", options: ["operational", "maintenance", "retired"] },
    { name: "last_maintenance", label: "Last maintenance", kind: "date" }, { name: "maintenance_due", label: "Maintenance due", kind: "date" },
    { name: "notes", label: "Notes", kind: "textarea" },
  ], roles: ["admin", "receptionist"], visibleRoles: ["admin", "receptionist", "trainer"] },
  { key: "feedback", label: "Feedback", description: "Member feedback and resolution status", group: "Insights", columns: ["id", "member_name", "rating", "message", "resolved", "created_at"], fields: [
    member, { name: "rating", label: "Rating (1–5)", kind: "number", required: true },
    { name: "message", label: "Feedback", kind: "textarea", required: true },
  ], roles: ["admin", "receptionist", "member"], visibleRoles: ["admin", "receptionist", "member"] },
  { key: "announcements", label: "Announcements", description: "Publish updates for targeted audiences", group: "Insights", columns: ["id", "title", "audience", "published_at", "expires_at"], fields: [
    { name: "title", label: "Title", required: true }, { name: "message", label: "Message", kind: "textarea", required: true },
    { name: "audience", label: "Audience", kind: "select", options: ["", "admin", "trainer", "receptionist", "member"] },
    { name: "expires_at", label: "Expires at", kind: "datetime-local" },
  ], roles: ["admin", "receptionist"], visibleRoles: ["admin", "receptionist", "trainer", "member"] },
  { key: "notifications", label: "Notifications", description: "Personal in-app updates and reminders", group: "Insights", columns: ["id", "title", "message", "read_at", "created_at"], fields: [], visibleRoles: ["admin", "receptionist", "trainer", "member"] },
  { key: "audit-logs", label: "Audit log", description: "Trace sensitive record changes by staff", group: "Insights", columns: ["id", "actor_name", "action", "object_type", "object_id", "created_at"], fields: [], visibleRoles: ["admin"] },
];
