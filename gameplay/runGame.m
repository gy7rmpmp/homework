function runGame()
% runGame - 聲控跑酷遊戲 (等級一~四)
% 操作：空白鍵跳躍 | R 重新開始 | ESC 離開
% 圖檔需與此程式放在同一資料夾：
%   back.jpg, ground2L.jpg, ground2C.jpg, ground2R.jpg
%   manRun.jpg, manJump.jpg

%% ===== 選擇等級 =====
choice = menu('選擇等級', ...
    '等級一 - 基本跑酷', ...
    '等級二 - 二段跳 + 固定高度障礙', ...
    '等級三 - 線性高度跳躍 + 隨機高度障礙', ...
    '等級四 - 等級三 + 金幣計分');
if choice == 0; return; end
level = choice;

%% ===== 讀取圖片 =====
imgBack    = imread('back.jpg');
imgGroundL = imread('ground2L.jpg');
imgGroundC = imread('ground2C.jpg');
imgGroundR = imread('ground2R.jpg');
imgRun     = imread('manRun.jpg');
imgJump    = imread('manJump.jpg');

%% ===== 視窗設定 =====
W = 660; H = 400;
fig = figure('Name', sprintf('跑酷遊戲 - 等級%d', level), ...
    'Position', [100 100 W H], ...
    'KeyPressFcn', @keyPress, ...
    'CloseRequestFcn', @closeFig, ...
    'MenuBar', 'none', 'ToolBar', 'none', ...
    'Resize', 'off');
ax = axes('Parent', fig, 'Position', [0 0 1 1]);
axis(ax, [0 W 0 H]); axis off; hold on;

%% ===== 遊戲參數 =====
GROUND_Y   = 80;
PLAYER_X   = 80;
GRAVITY    = -18;
JUMP1_VY   = 22;
JUMP2_VY   = 20;
STE_MIN    = 1; STE_MAX = 10; STE_MULT = 2;
SCROLL_SPEED = 5;

%% ===== 初始化狀態 =====
state = initState();

%% ===== 障礙物 & 金幣結構 =====
obs  = struct('x', [], 'y', []);
coin = struct('x', [], 'y', [], 'collected', []);
groundScroll = 0;
dt = 0.03;

%% ===== 主迴圈 =====
while state.running && ishandle(fig)

    if ~state.gameOver

        %--- 物理更新 ---
        if ~state.onGround
            state.velY = state.velY + GRAVITY * dt;
        end
        state.playerY = state.playerY + state.velY;

        if state.playerY <= GROUND_Y
            state.playerY  = GROUND_Y;
            state.velY     = 0;
            state.onGround = true;
            state.jumpCount = 0;
        end

        % 地板捲動
        groundScroll = mod(groundScroll + SCROLL_SPEED, 60);

        %--- 障礙物（等級 2~4）---
        if level >= 2
            % 移動
            if ~isempty(obs.x)
                obs.x = obs.x - SCROLL_SPEED;
                keep = obs.x > -30;
                obs.x = obs.x(keep);
                obs.y = obs.y(keep);
            end

            % 新增障礙
            spawnObs = isempty(obs.x) || obs.x(end) < W - 180 - rand*120;
            if spawnObs
                newX = W + 20;
                if level == 2
                    newY = GROUND_Y + 80;
                else
                    ste  = STE_MIN + rand*(STE_MAX - STE_MIN);
                    newY = GROUND_Y + round(ste * STE_MULT) * 5 + 20;
                    newY = min(newY, H - 40);
                end
                obs.x(end+1) = newX;
                obs.y(end+1) = newY;
            end

            % 碰撞偵測
            for i = 1:length(obs.x)
                if PLAYER_X+26 > obs.x(i) && PLAYER_X < obs.x(i)+30 && ...
                   state.playerY+26 > obs.y(i) && state.playerY < obs.y(i)+30
                    state.gameOver = true;
                end
            end
        end

        %--- 金幣（等級 4）---
        if level == 4
            % 移動
            if ~isempty(coin.x)
                coin.x = coin.x - SCROLL_SPEED;
                keep = coin.x > -20;
                coin.x         = coin.x(keep);
                coin.y         = coin.y(keep);
                coin.collected = coin.collected(keep);
            end

            % 新增金幣
            spawnCoin = isempty(coin.x) || coin.x(end) < W - 100 - rand*200;
            if spawnCoin
                coin.x(end+1)         = W + 10;
                coin.y(end+1)         = GROUND_Y + 20 + rand*180;
                coin.collected(end+1) = false;
            end

            % 收集金幣
            for i = 1:length(coin.x)
                if ~coin.collected(i)
                    if PLAYER_X+26 > coin.x(i) && PLAYER_X < coin.x(i)+20 && ...
                       state.playerY+26 > coin.y(i) && state.playerY < coin.y(i)+20
                        coin.collected(i) = true;
                        state.coinScore = state.coinScore + 10;
                    end
                end
            end
        end

        state.score = state.score + 1;
    end

    %--- 繪圖 ---
    cla(ax);

    % 背景
    image(ax, [0 W], [0 H], flipud(imgBack));

    % 地板
    tileW = 60; xStart = -groundScroll;
    while xStart < W
        if xStart <= 0
            img = imgGroundL;
        elseif xStart + tileW >= W
            img = imgGroundR;
        else
            img = imgGroundC;
        end
        image(ax, [xStart xStart+tileW], [0 tileW], flipud(img));
        xStart = xStart + tileW;
    end

    % 障礙物
    if level >= 2
        for i = 1:length(obs.x)
            rectangle(ax, 'Position', [obs.x(i) obs.y(i) 30 30], ...
                'FaceColor', [0.75 0.38 0.08], 'EdgeColor', [0.4 0.2 0]);
            text(ax, obs.x(i)+7, obs.y(i)+18, '?', ...
                'Color', 'w', 'FontSize', 14, 'FontWeight', 'bold');
        end
    end

    % 金幣
    if level == 4
        for i = 1:length(coin.x)
            if ~coin.collected(i)
                rectangle(ax, 'Position', [coin.x(i) coin.y(i) 18 18], ...
                    'Curvature', [1 1], ...
                    'FaceColor', [1.0 0.82 0.0], 'EdgeColor', [0.8 0.55 0.0], ...
                    'LineWidth', 1.5);
                text(ax, coin.x(i)+3, coin.y(i)+11, '$', ...
                    'Color', [0.6 0.3 0], 'FontSize', 9, 'FontWeight', 'bold');
            end
        end
    end

    % 玩家
    if state.onGround
        image(ax, [PLAYER_X PLAYER_X+32], [state.playerY state.playerY+32], flipud(imgRun));
    else
        image(ax, [PLAYER_X PLAYER_X+32], [state.playerY state.playerY+32], flipud(imgJump));
    end

    % HUD - 分數
    if level == 4
        totalScore = floor(state.score/10) + state.coinScore;
        text(ax, 10, H-12, sprintf('分數: %d  (金幣: %d)', totalScore, state.coinScore), ...
            'Color', 'w', 'FontSize', 13, 'FontWeight', 'bold');
    else
        text(ax, 10, H-12, sprintf('分數: %d', floor(state.score/10)), ...
            'Color', 'w', 'FontSize', 13, 'FontWeight', 'bold');
    end
    text(ax, 10, H-30, sprintf('等級 %d', level), 'Color', 'yellow', 'FontSize', 10);

    % 操作提示
    switch level
        case 1; hint = '空白鍵：跳躍';
        case 2; hint = '空白鍵：跳躍（可二段跳）';
        case 3; hint = '空白鍵：跳躍（高度隨機）';
        case 4; hint = '空白鍵：跳躍  收集金幣得分';
    end
    text(ax, W-8, H-12, hint, 'Color', 'w', 'FontSize', 10, 'HorizontalAlignment', 'right');

    % Game Over 畫面
    if state.gameOver
        if level == 4
            finalScore = floor(state.score/10) + state.coinScore;
        else
            finalScore = floor(state.score/10);
        end
        text(ax, W/2, H/2+30, 'GAME OVER', ...
            'Color', 'red', 'FontSize', 34, 'FontWeight', 'bold', ...
            'HorizontalAlignment', 'center');
        text(ax, W/2, H/2-10, sprintf('最終分數: %d', finalScore), ...
            'Color', 'white', 'FontSize', 18, 'HorizontalAlignment', 'center');
        if level == 4
            text(ax, W/2, H/2-35, sprintf('金幣得分: %d', state.coinScore), ...
                'Color', [1 0.85 0], 'FontSize', 14, 'HorizontalAlignment', 'center');
        end
        text(ax, W/2, H/2-60, 'R 重新開始  |  ESC 離開', ...
            'Color', 'yellow', 'FontSize', 12, 'HorizontalAlignment', 'center');
    end

    axis(ax, [0 W 0 H]); axis off;
    drawnow;
    pause(dt);
end

if ishandle(fig); close(fig); end

%% ===== 初始化函式 =====
function s = initState()
    s.running    = true;
    s.playerY    = GROUND_Y;
    s.velY       = 0;
    s.onGround   = true;
    s.jumpCount  = 0;
    s.score      = 0;
    s.coinScore  = 0;
    s.gameOver   = false;
end

%% ===== 按鍵處理 =====
function keyPress(~, e)
    switch e.Key
        case 'space'
            if state.gameOver; return; end
            if state.onGround
                if level == 3 || level == 4
                    ste = STE_MIN + rand*(STE_MAX - STE_MIN);
                    state.velY = ste * STE_MULT * 0.8 + 8;
                else
                    state.velY = JUMP1_VY;
                end
                state.onGround  = false;
                state.jumpCount = 1;
            elseif level >= 2 && state.jumpCount < 2
                state.velY      = JUMP2_VY;
                state.jumpCount = 2;
            end

        case 'r'
            if state.gameOver
                state = initState();
                obs.x = []; obs.y = [];
                coin.x = []; coin.y = []; coin.collected = [];
                groundScroll = 0;
            end

        case 'escape'
            state.running = false;
    end
end

function closeFig(~, ~)
    state.running = false;
    delete(fig);
end

end
