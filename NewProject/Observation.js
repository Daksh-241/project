const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const ObservationSchema = new Schema({
  status: {
    type: String,
    enum: ['registered', 'preliminary', 'final', 'amended', 'corrected', 'cancelled', 'entered-in-error', 'unknown'],
    default: 'final',
  },
  code: {
    coding: [{
      system: String,
      code: String,
      display: String,
    }],
    text: String,
  },
  subject: {
    type: Schema.Types.ObjectId,
    ref: 'Patient', // Reference to the Patient model
    required: true,
  },
  effectiveDateTime: {
    type: Date,
  },
  valueQuantity: {
    value: Number,
    unit: String,
    system: String,
    code: String,
  },
  issued: {
    type: Date,
    default: Date.now,
  },
});

module.exports = mongoose.model('Observation', ObservationSchema);