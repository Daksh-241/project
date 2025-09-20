const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const PatientSchema = new Schema({
  identifier: [{
    system: String,
    value: String,
  }],
  name: [{
    family: { type: String, required: true },
    given: [String],
  }],
  gender: {
    type: String,
    enum: ['male', 'female', 'other', 'unknown'],
  },
  birthDate: {
    type: Date,
  },
  // Add other fields you need like address, telecom, etc.
  createdAt: {
    type: Date,
    default: Date.now,
  },
});

module.exports = mongoose.model('Patient', PatientSchema);