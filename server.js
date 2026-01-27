const express = require("express");
const dotenv = require("dotenv");
const cors = require("cors");
const connectDB = require("./config/db");

dotenv.config();
connectDB();

const app = express();
app.use(cors());
app.use(express.json());
app.use("/api/predict", require("./routes/predictionRoutes"));
app.use("/api/auth", require("./routes/authRoutes"));



app.get("/", (req, res) => {
  res.send("Cancer Prediction Backend Running");
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
