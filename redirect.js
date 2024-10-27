const express = require("express");
const session = require("express-session");
const bodyParser = require("body-parser");
const cors = require("cors");
const path = require("path");
const app = express();
const PORT = 3000;

// Middleware setup
app.use(
  cors({
    origin: "http://127.0.0.1:5000",
    credentials: true,
  })
);
app.use(bodyParser.json());
app.use(
  session({
    secret: "522cf0143346652762d42387e84abe7a",
    resave: false,
    saveUninitialized: true,
    cookie: { secure: false, maxAge: null },
  })
);

// Serve static files
app.use(express.static("public"));

// Specific API route
app.get("/api/entries", (req, res) => {
  // Your API logic here
  res.json({ message: "API Data" });
});

// Logout route
app.get("/logout", (req, res) => {
  // Your logout logic here
  req.session.destroy((err) => {
    if (err) {
      return res.status(500).send("Failed to log out");
    }
    res.send("Logged out");
  });
});

// Catch-all redirect for any other request
app.get("*", (req, res) => {
  console.log(`Redirecting all traffic from ${req.originalUrl}`);
  res.redirect("http://127.0.0.1:5000");
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
