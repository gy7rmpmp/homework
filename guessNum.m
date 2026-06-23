function guessNum(minBound, maxBound)
% guessNum - A number guessing game
% Usage: guessNum(1, 100)

    a = randperm(maxBound - minBound + 1);
    answer = a(1) + minBound - 1;
    count = 0;

    lo = minBound;
    hi = maxBound;

    disp('Jarvus made a simple game!');
    fprintf('You can enter a number between %d and %d.\n', lo, hi);

    while true
        guess = input('please enter your number:');

        % Check out of range
        if guess < lo || guess > hi
            disp('Wrong area!');
            fprintf('You can enter a number between %d and %d.\n', lo, hi);
            continue;
        end

        count = count + 1;

        if guess < answer
            lo = guess;
            fprintf('You can enter a number between %d and %d.\n', lo, hi);
        elseif guess > answer
            hi = guess;
            fprintf('You can enter a number between %d and %d.\n', lo, hi);
        else
            fprintf('Win! You take %d times.\n', count);
            again = input('Do you want to play again? (1:YES/2:NO):');
            if again == 1
                guessNum(minBound, maxBound);
            end
            return;
        end
    end
end
