"""
岛屿数量问题 — Number of Islands

给定一个由 '1'（陆地）和 '0'（水）组成的二维网格，计算岛屿的数量。
一个岛被水包围，并且通过水平或垂直连接相邻的陆地而形成。
"""


def num_islands(grid: list[list[str]]) -> int:
    """
    使用 DFS 遍历计算岛屿数量。

    遍历每个格子，遇到 '1' 时计数 +1，并用 DFS 将整个岛屿标记为已访问（设为 '0'）。
    """
    if not grid or not grid[0]:
        return 0

    rows, cols = len(grid), len(grid[0])
    count = 0

    def dfs(r: int, c: int) -> None:
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != "1":
            return
        grid[r][c] = "0"  # 标记已访问
        dfs(r - 1, c)
        dfs(r + 1, c)
        dfs(r, c - 1)
        dfs(r, c + 1)

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1":
                count += 1
                dfs(r, c)

    return count


# ---------- 测试用例 ----------

if __name__ == "__main__":
    # 示例 1
    grid1 = [
        ["1", "1", "1", "1", "0"],
        ["1", "1", "0", "1", "0"],
        ["1", "1", "0", "0", "0"],
        ["0", "0", "0", "0", "0"],
    ]
    assert num_islands(grid1) == 1, f"Expected 1, got {num_islands(grid1)}"

    # 示例 2
    grid2 = [
        ["1", "1", "0", "0", "0"],
        ["1", "1", "0", "0", "0"],
        ["0", "0", "1", "0", "0"],
        ["0", "0", "0", "1", "1"],
    ]
    assert num_islands(grid2) == 3, f"Expected 3, got {num_islands(grid2)}"

    # 空网格
    assert num_islands([]) == 0

    # 单个格子
    assert num_islands([["1"]]) == 1
    assert num_islands([["0"]]) == 0

    print("所有测试通过 ✅")
