package dev.danvega.todos;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Keeps track of todos for the demo.
 *
 * @author Dan Vega
 * @see Todo
 */
@SuppressWarnings("unused")
public class TodoService {

    private static final int MAX_TODOS = 100;
    private final List<Todo> todos = new ArrayList<>();

    public Todo create(String title, LocalDate due) {
        // TODO: validate the title length
        if (todos.size() >= MAX_TODOS) {
            throw new IllegalStateException("Too many todos: " + todos.size());
        }
        var todo = new Todo(todos.size() + 1, title, due, false);
        todos.add(todo);
        return todo;
    }

    public List<Todo> findOpen() {
        return todos.stream()
                .filter(t -> !t.done())
                .toList();
    }

    @Deprecated
    public String summary() {
        String status = todos.isEmpty() ? "nothing to do\n" : "%d open".formatted(findOpen().size());
        return status + missingMethod();
    }

    record Todo(int id, String title, LocalDate due, boolean done) {}
}
