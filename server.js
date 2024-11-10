const express = require("express");
const session = require("express-session");
const bodyParser = require("body-parser");
const path = require("path");
const cors = require("cors");
const { MongoClient, ObjectId } = require("mongodb");

const app = express();
const PORT = 3000;
const dbUrl = "mongodb://localhost:27017";
const dbName = "trading_tracker_db";
const client = new MongoClient(dbUrl, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

let db, entriesCollection;

// Enable CORS, allowing requests from specific origins
app.use(
  cors({
    origin: ["http://127.0.0.1:5000", "http://localhost:5000"], // Include additional origins if needed
    credentials: true,
  })
);

// Session configuration
app.use(
  session({
    secret: "522cf0143346652762d42387e84abe7a",
    resave: false,
    saveUninitialized: true,
    cookie: { secure: process.env.NODE_ENV === "production" }, // Use secure cookies in production
  })
);

// Serve static files
app.use(express.static("public"));

// Parse JSON bodies
app.use(bodyParser.json());

// Initialize MongoDB connection and collections
client
  .connect()
  .then(() => {
    db = client.db(dbName);
    entriesCollection = db.collection("entries");
    console.log("Connected to MongoDB");
  })
  .catch((err) => console.log("MongoDB connection error:", err));

// Authentication check middleware
function isAuthenticated(req, res, next) {
  if (req.session && req.session.user) {
    next();
  } else {
    res.redirect("http://127.0.0.1:5000/login"); // Redirect to login if not authenticated
  }
}

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
  const userContact = req.query.user;
  req.session.user = userContact; // Store the user in session
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

// API routes for user-specific data operations
app.get("/api/entries", isAuthenticated, async (req, res) => {
  try {
    const userContact = req.session.user;
    const entries = await entriesCollection
      .find({ user_contact: userContact })
      .toArray();
    res.json({ entries });
  } catch (error) {
    console.error("Error fetching entries:", error);
    res.status(500).json({ error: "Failed to fetch entries" });
  }
});

app.post("/api/entries", isAuthenticated, async (req, res) => {
  try {
    const userContact = req.session.user;
    const newEntry = req.body;
    newEntry.user_contact = userContact; // Associate entry with user
    await entriesCollection.insertOne(newEntry);
    res.status(201).json({ message: "Entry added successfully" });
  } catch (error) {
    console.error("Error adding entry:", error);
    res.status(500).json({ error: "Failed to add entry" });
  }
});

// Update an entry
app.put("/api/entries/:id", isAuthenticated, async (req, res) => {
  try {
    const userContact = req.session.user;
    const entryId = req.params.id;
    const updatedEntry = req.body;

    const result = await entriesCollection.updateOne(
      { _id: new ObjectId(entryId), user_contact: userContact },
      { $set: updatedEntry }
    );

    if (result.matchedCount === 0) {
      return res
        .status(404)
        .json({ message: "Entry not found or not authorized" });
    }
    res.json({ message: "Entry updated successfully" });
  } catch (error) {
    console.error("Error updating entry:", error);
    res.status(500).json({ error: "Failed to update entry" });
  }
});

// Delete an entry
app.delete("/api/entries/:id", isAuthenticated, async (req, res) => {
  try {
    const userContact = req.session.user;
    const entryId = req.params.id;

    const result = await entriesCollection.deleteOne({
      _id: new ObjectId(entryId),
      user_contact: userContact,
    });

    if (result.deletedCount === 0) {
      return res
        .status(404)
        .json({ message: "Entry not found or not authorized" });
    }
    res.json({ message: "Entry deleted successfully" });
  } catch (error) {
    console.error("Error deleting entry:", error);
    res.status(500).json({ error: "Failed to delete entry" });
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

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
