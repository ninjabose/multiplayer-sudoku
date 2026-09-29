export default function Board({
  puzzle,
  grid,
  solution,
  selected,
  onSelect,
  ended,
}) {
  const display = solution || grid
  if (!display) {
    return <div className="board empty-board">Waiting for puzzle…</div>
  }

  return (
    <div className="board" role="grid" aria-label="Sudoku board">
      {display.map((row, r) =>
        row.map((value, c) => {
          const isClue = puzzle?.[r]?.[c] !== 0
          const isSelected = selected?.row === r && selected?.col === c
          const thickRight = c === 2 || c === 5
          const thickBottom = r === 2 || r === 5
          const classes = [
            'cell',
            isClue ? 'clue' : 'entry',
            isSelected ? 'selected' : '',
            thickRight ? 'thick-right' : '',
            thickBottom ? 'thick-bottom' : '',
            solution && !isClue ? 'revealed' : '',
          ]
            .filter(Boolean)
            .join(' ')

          return (
            <button
              key={`${r}-${c}`}
              type="button"
              className={classes}
              disabled={ended || isClue}
              onClick={() => onSelect({ row: r, col: c })}
            >
              {value || ''}
            </button>
          )
        }),
      )}
    </div>
  )
}
