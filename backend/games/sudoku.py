"""Täglicher Sudoku-Generator (mittlerer Schwierigkeitsgrad)."""
import random


def _make_solved_grid() -> list:
    """Erzeugt ein vollständig gelöstes 9x9 Sudoku-Gitter per Backtracking."""
    grid = [[0] * 9 for _ in range(9)]

    def valid(r, c, val):
        if val in grid[r]:
            return False
        if val in (grid[i][c] for i in range(9)):
            return False
        br, bc = 3 * (r // 3), 3 * (c // 3)
        for i in range(br, br + 3):
            for j in range(bc, bc + 3):
                if grid[i][j] == val:
                    return False
        return True

    def fill(pos=0):
        if pos == 81:
            return True
        r, c = divmod(pos, 9)
        candidates = list(range(1, 10))
        random.shuffle(candidates)
        for val in candidates:
            if valid(r, c, val):
                grid[r][c] = val
                if fill(pos + 1):
                    return True
                grid[r][c] = 0
        return False

    fill()
    return grid


def _count_solutions(grid: list, limit: int = 2) -> int:
    """Zählt Lösungen bis zu 'limit' (für Eindeutigkeits-Check)."""
    grid = [row[:] for row in grid]
    count = 0

    def valid(r, c, val):
        if val in grid[r]:
            return False
        if val in (grid[i][c] for i in range(9)):
            return False
        br, bc = 3 * (r // 3), 3 * (c // 3)
        for i in range(br, br + 3):
            for j in range(bc, bc + 3):
                if grid[i][j] == val:
                    return False
        return True

    def find_empty():
        for r in range(9):
            for c in range(9):
                if grid[r][c] == 0:
                    return r, c
        return None

    def solve():
        nonlocal count
        if count >= limit:
            return
        pos = find_empty()
        if pos is None:
            count += 1
            return
        r, c = pos
        for val in range(1, 10):
            if valid(r, c, val):
                grid[r][c] = val
                solve()
                grid[r][c] = 0
                if count >= limit:
                    return

    solve()
    return count


def generate_sudoku(difficulty: str = "medium") -> dict:
    """Erzeugt ein Sudoku-Rätsel mit eindeutiger Lösung.

    difficulty: 'easy' | 'medium' | 'hard' - steuert die Anzahl entfernter Zellen.
    """
    holes_by_difficulty = {"easy": 36, "medium": 46, "hard": 54}
    target_holes = holes_by_difficulty.get(difficulty, 46)

    solution = _make_solved_grid()
    puzzle = [row[:] for row in solution]

    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)

    removed = 0
    for r, c in cells:
        if removed >= target_holes:
            break
        backup = puzzle[r][c]
        puzzle[r][c] = 0
        if _count_solutions(puzzle, limit=2) != 1:
            puzzle[r][c] = backup
        else:
            removed += 1

    return {
        "puzzle": puzzle,
        "solution": solution,
        "difficulty": difficulty,
        "holes": removed,
    }


if __name__ == "__main__":
    data = generate_sudoku()
    for row in data["puzzle"]:
        print(" ".join(str(v) if v else "." for v in row))
    print("Entfernte Zellen:", data["holes"])
