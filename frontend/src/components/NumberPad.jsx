export default function NumberPad({ onDigit, onClear, disabled }) {
  return (
    <div className="number-pad">
      {Array.from({ length: 9 }, (_, i) => i + 1).map((digit) => (
        <button
          key={digit}
          type="button"
          className="pad-btn"
          disabled={disabled}
          onClick={() => onDigit(digit)}
        >
          {digit}
        </button>
      ))}
      <button
        type="button"
        className="pad-btn pad-clear"
        disabled={disabled}
        onClick={onClear}
      >
        Clear
      </button>
    </div>
  )
}
