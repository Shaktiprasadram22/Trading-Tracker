const express = require("express");
const session = require("express-session");
const bodyParser = require("body-parser");
const path = require("path");
const fs = require("fs");
const cors = require("cors");

const app = express();
const PORT = 3000;
const dataFilePath = path.join(__dirname, "data.json");

// Enable CORS, allowing requests from the specified origin
app.use(
  cors({
    origin: "http://127.0.0.1:5000",
    credentials: true,
  })
);

// Session configuration
app.use(
  session({
    secret: "522cf0143346652762d42387e84abe7a",
    resave: false,
    saveUninitialized: true,
    cookie: { secure: false }, // Use `secure: true` in production with HTTPS
  })
);

// Serve static files
app.use(express.static("public"));

// Parse JSON bodies
app.use(bodyParser.json());

// Authentication check middleware
function isAuthenticated(req, res, next) {
  if (req.session && req.session.user) {
    next();
  } else {
    res.redirect("http://127.0.0.1:5000/login"); // Redirect to login if not authenticated
  }
}

// Apply authentication check globally except for allowed paths
app.use((req, res, next) => {
  if (["/login", "/set-session"].includes(req.path) || req.session.user) {
    next();
  } else {
    res.redirect("http://127.0.0.1:5000/login");
  }
});

// Root route - always redirect to the login page
app.get("/", (req, res) => {
  res.redirect("http://127.0.0.1:5000/login");
});

// Protected route for the main page
app.get("/index", isAuthenticated, (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

// Mock login page for demonstration
app.get("/login", (req, res) => {
  res.send("This is the login page. Please log in.");
});

// Route for setting the session after login
app.get("/set-session", (req, res) => {
  req.session.user = { contact: "user_contact" }; // Simulate a user session
  res.redirect("/index");
});

// Logout route
app.get("/logout", (req, res) => {
  req.session.destroy((err) => {
    if (err) {
      console.error("Failed to destroy the session:", err);
      return res.status(500).send("Failed to log out");
    }
    res.clearCookie("connect.sid", { path: "/" });
    res.redirect("http://127.0.0.1:5000/login");
  });
});

// Function to load and save data
function loadEntries() {
  try {
    const fileData = fs.readFileSync(dataFilePath, "utf8");
    return JSON.parse(fileData);
  } catch (err) {
    console.error("Error reading data file:", err);
    return [];
  }
}

function saveEntries(entries) {
  try {
    const data = JSON.stringify(entries, null, 2);
    fs.writeFileSync(dataFilePath, data, "utf8");
  } catch (err) {
    console.error("Error writing to data file:", err);
    throw err;
  }
}

// API routes for data operations
app.get("/api/entries", isAuthenticated, (req, res) => {
  res.json(loadEntries());
});

app.post("/api/entries", isAuthenticated, (req, res) => {
  const entries = loadEntries();
  entries.push(req.body);
  try {
    saveEntries(entries);
    res.status(201).json({ message: "Entry added successfully." });
  } catch (error) {
    res.status(500).json({ error: "Failed to save the entry" });
  }
});

app.get("/api/entries/:index", isAuthenticated, (req, res) => {
  const index = parseInt(req.params.index);
  const entries = loadEntries();
  if (index >= 0 && index < entries.length) {
    res.json(entries[index]);
  } else {
    res.status(404).json({ error: "Entry not found" });
  }
});

app.put("/api/entries/:index", isAuthenticated, (req, res) => {
  const index = parseInt(req.params.index);
  let entries = loadEntries();
  if (index >= 0 && index < entries.length) {
    entries[index] = req.body;
    try {
      saveEntries(entries);
      res.json({ message: "Entry updated successfully." });
    } catch (error) {
      res.status(500).json({ error: "Failed to update the entry" });
    }
  } else {
    res.status(404).json({ error: "Entry not found" });
  }
});

app.delete("/api/entries/:index", isAuthenticated, (req, res) => {
  const index = parseInt(req.params.index);
  let entries = loadEntries();
  if (index >= 0 && index < entries.length) {
    entries.splice(index, 1);
    try {
      saveEntries(entries);
      res.json({ message: "Entry deleted successfully." });
    } catch (error) {
      res.status(500).json({ error: "Failed to delete the entry" });
    }
  } else {
    res.status(404).json({ error: "Entry not found" });
  }
});

// Error handling for non-existent routes
app.use((req, res) => {
  res.status(404).json({ error: "Not Found" });
});

// Generic error handler
app.use((err, req, res, next) => {
  console.error("Unhandled error:", err);
  res.status(500).json({ error: "Internal Server Error" });
});

//Start the server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
